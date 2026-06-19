"""Run the QuestDB bulk-write benchmark across Pathway worker counts.

Two containers (QuestDB + Pathway). The dataset is generated as CSV shards; each
measured run reads the shard directory (bounded, ``mode="static"``) and writes
every row to QuestDB over the InfluxDB Line Protocol. The sharded input lets the
filesystem reader parallelize across workers. For each worker count the run is
repeated ``--reps`` times and the median is reported.

Usage:
    python run_questdb_bulk_write.py                       # workers 1 2 4 8
    python run_questdb_bulk_write.py --workers 8 --reps 1  # quick check
"""

import argparse
import json
import os
import re
import statistics
import subprocess
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

PROJECT = (os.environ.get("USER", "qdbbulk") + "_qdbbulk").replace(".", "_")
COMPOSE = [
    "docker",
    "compose",
    "--env-file",
    "docker-compose/variables.env",
    "-f",
    "docker-compose/docker-compose.yml",
    "-p",
    PROJECT,
]
TABLE = "bench_out"


def sh(cmd, **kw):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    return subprocess.run(cmd, **kw)


def qdb_exec(sql: str):
    port = os.environ.get("QUESTDB_HTTP_PORT", "29000")
    url = f"http://127.0.0.1:{port}/exec?query=" + urllib.parse.quote(sql)
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode())


def qdb_scalar(sql: str):
    return qdb_exec(sql)["dataset"][0][0]


def qdb_count() -> int:
    try:
        return int(qdb_scalar(f"SELECT count() FROM '{TABLE}'"))
    except Exception:
        return -1


def verify_correctness(rows: int) -> tuple[bool, dict]:
    """Check, over the QuestDB HTTP endpoint, that every row landed intact.

    Runs *after* the measured run, so it is never part of the timed window. The
    generated data has `k` = 0..rows-1 and `name` = "item_<k>", which makes a
    handful of aggregates a strong end-to-end integrity check: exact row count,
    the key range and sum (catches missing/duplicate/garbled keys), the derived
    `name` column, and the absence of nulls in `value`/`flag`.
    """
    expected_sum = rows * (rows - 1) // 2
    checks = {
        "count": int(qdb_scalar(f"SELECT count() FROM '{TABLE}'")),
        "min_k": int(qdb_scalar(f"SELECT min(k) FROM '{TABLE}'")),
        "max_k": int(qdb_scalar(f"SELECT max(k) FROM '{TABLE}'")),
        "sum_k": int(qdb_scalar(f"SELECT sum(k) FROM '{TABLE}'")),
        "bad_name": int(
            qdb_scalar(
                f"SELECT count() FROM '{TABLE}' WHERE name <> concat('item_', k)"
            )
        ),
        "null_cols": int(
            qdb_scalar(
                f"SELECT count() FROM '{TABLE}' "
                "WHERE value IS NULL OR flag IS NULL OR name IS NULL"
            )
        ),
    }
    ok = (
        checks["count"] == rows
        and checks["min_k"] == 0
        and checks["max_k"] == rows - 1
        and checks["sum_k"] == expected_sum
        and checks["bad_name"] == 0
        and checks["null_cols"] == 0
    )
    return ok, checks


def gen_dataset(rows: int, shards: int) -> None:
    out = os.path.join("datasets", f"input_{rows}")
    if os.path.isdir(out) and os.listdir(out):
        print(f"dataset present: {out}")
        return
    sh(
        [
            "python3",
            "datasets/questdb-bulk-gen.py",
            "--rows",
            str(rows),
            "--shards",
            str(shards),
            "--output-dir",
            out,
        ]
    )


def run_measured(rows: int, workers: int) -> tuple[float, bool]:
    qdb_exec(f"DROP TABLE IF EXISTS '{TABLE}'")
    env = dict(os.environ)
    env["DATASET_SIZE"] = str(rows)
    env["PATHWAY_THREADS"] = str(workers)
    res = subprocess.run(
        COMPOSE + ["run", "--rm", "pathway"], env=env, capture_output=True, text=True
    )
    out = res.stdout + res.stderr
    elapsed = re.search(r"ELAPSED_SECONDS=([0-9.]+)", out)
    if not elapsed:
        print(out)
        raise SystemExit("pathway run did not report ELAPSED_SECONDS")
    # Verification below is NOT part of the measured time (`elapsed` is the
    # wall-clock of pw.run() reported by the container). ILP-over-HTTP commits
    # asynchronously, so first wait for the WAL apply to catch up, then run the
    # integrity checks.
    deadline = time.monotonic() + 60
    while qdb_count() < rows and time.monotonic() < deadline:
        time.sleep(0.5)
    ok, checks = verify_correctness(rows)
    if not ok:
        print(f"  CORRECTNESS CHECK FAILED: {checks}")
    return float(elapsed.group(1)), ok


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=20_000_000)
    p.add_argument("--shards", type=int, default=64)
    p.add_argument("--workers", type=int, nargs="+", default=[1, 2, 4, 8])
    p.add_argument("--reps", type=int, default=3)
    args = p.parse_args()

    if not os.environ.get("PATHWAY_LICENSE_KEY"):
        raise SystemExit(
            "PATHWAY_LICENSE_KEY is not set. The QuestDB output connector is a "
            "licensed feature and a key must be provided:\n"
            "    export PATHWAY_LICENSE_KEY=...\n"
            "Get a key at https://pathway.com/get-license/"
        )

    gen_dataset(args.rows, args.shards)
    sh(COMPOSE + ["build", "pathway"])
    sh(COMPOSE + ["up", "-d", "--wait", "questdb"])

    results = []
    try:
        for w in args.workers:
            runs = [run_measured(args.rows, w) for _ in range(args.reps)]
            times = [t for t, _ in runs]
            median = statistics.median(times)
            results.append(
                {
                    "workers": w,
                    "median": median,
                    "rows_per_second": args.rows / median,
                    "ok": all(ok for _, ok in runs),
                    "runs": times,
                }
            )
    finally:
        sh(COMPOSE + ["down", "-v"])

    base = results[0]["rows_per_second"]
    print(
        f"\n==================== RESULTS  ({args.rows:,} rows, "
        f"median of {args.reps}) ===================="
    )
    print(
        f"{'workers':>8}{'median_s':>11}{'rows/s':>14}{'speedup':>9}{'ok':>5}   runs(s)"
    )
    for r in results:
        runs_str = ", ".join(f"{t:.1f}" for t in r["runs"])
        print(
            f"{r['workers']:>8}{r['median']:>11.2f}{r['rows_per_second']:>14,.0f}"
            f"{r['rows_per_second'] / base:>8.2f}x{str(r['ok']):>5}   {runs_str}"
        )


if __name__ == "__main__":
    main()
