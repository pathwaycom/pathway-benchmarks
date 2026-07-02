"""Run the MySQL bulk-write benchmark across Pathway worker counts.

Two containers (MySQL + Pathway). The dataset is generated as CSV shards; each
measured run reads the shard directory (bounded, ``mode="static"``) and writes
every row to MySQL with ``pw.io.mysql.write`` (batched INSERT statements). The sharded
input lets the filesystem reader parallelize the read across workers (each shard
is owned by exactly one worker, chosen by a stable hash of its path), so the
worker sweep exercises both the parallel read and the parallel write. For each
worker count the run is repeated ``--reps`` times and the median is reported.

This benchmark is deliberately the QuestDB/PostgreSQL bulk-write benchmark with
the database swapped for MySQL: same dataset, same core pinning, same end-to-end
timing and out-of-band correctness verification.

Usage:
    python run_mysql_bulk_write.py                       # workers 1 2 4 8
    python run_mysql_bulk_write.py --workers 8 --reps 1  # quick check
    python run_mysql_bulk_write.py --rows 200000 --workers 1 --reps 1  # calibration probe
"""

import argparse
import os
import re
import statistics
import subprocess
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

SHARED_DATASETS = os.path.join(ROOT, "..", "datasets-shared")
GEN = os.path.join(SHARED_DATASETS, "bulk-gen.py")

PROJECT = (os.environ.get("USER", "mysqlbulk") + "_mysqlbulk").replace(".", "_")
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


def mysql_q(sql: str) -> str:
    """Run a SQL statement inside the MySQL container (over TCP to itself) and
    return the raw tab-separated output. Used only for setup/verification, never
    inside the timed window."""
    res = subprocess.run(
        COMPOSE
        + [
            "exec",
            "-T",
            "mysql",
            "mysql",
            "-uroot",
            "-prootpass",
            "testdb",
            "-N",
            "-B",
            "-e",
            sql,
        ],
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


def my_count() -> int:
    try:
        return int(mysql_q(f"SELECT count(*) FROM {TABLE}"))
    except ValueError:
        return -1


def verify_correctness(rows: int) -> tuple[bool, dict]:
    """Check, over the MySQL wire protocol, that every row landed intact.

    Runs *after* the measured run, so it is never part of the timed window. The
    generated data has ``k`` = 0..rows-1 and ``name`` = "item_<k>", which makes a
    handful of aggregates a strong end-to-end integrity check: exact row count,
    the key range and sum (catches missing/duplicate/garbled keys), the derived
    ``name`` column, the absence of nulls, and — specific to the stream-of-changes
    format ``pw.io.mysql.write`` appends — that every row is an insertion
    (``diff = 1``), so ``sum(diff)`` must equal the row count.
    """
    expected_sum = rows * (rows - 1) // 2
    row = mysql_q(
        f"SELECT count(*), coalesce(min(k), -1), coalesce(max(k), -1), "
        f"coalesce(sum(k), 0), coalesce(sum(`diff`), 0), "
        f"coalesce(sum(name <> concat('item_', k)), 0), "
        f"coalesce(sum(value IS NULL OR flag IS NULL OR name IS NULL), 0) "
        f"FROM {TABLE}"
    )
    fields = [int(x) for x in row.split("\t")]
    keys = ["count", "min_k", "max_k", "sum_k", "sum_diff", "bad_name", "null_cols"]
    checks = dict(zip(keys, fields))
    ok = (
        checks["count"] == rows
        and checks["min_k"] == 0
        and checks["max_k"] == rows - 1
        and checks["sum_k"] == expected_sum
        and checks["sum_diff"] == rows
        and checks["bad_name"] == 0
        and checks["null_cols"] == 0
    )
    return ok, checks


def gen_dataset(rows: int, shards: int) -> None:
    out = os.path.join(SHARED_DATASETS, f"input_{rows}")
    if os.path.isdir(out) and os.listdir(out):
        print(f"dataset present: {out}")
        return
    sh(
        [
            "python3",
            GEN,
            "--rows",
            str(rows),
            "--shards",
            str(shards),
            "--output-dir",
            out,
        ]
    )


def run_measured(rows: int, batch: int, workers: int) -> tuple[float, bool]:
    mysql_q(f"DROP TABLE IF EXISTS {TABLE}")
    env = dict(os.environ)
    env["DATASET_SIZE"] = str(rows)
    env["BATCH_SIZE"] = str(batch)
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
    # wall-clock of pw.run() reported by the container). Give the server a brief
    # grace window before the integrity checks just in case.
    deadline = time.monotonic() + 120
    while my_count() < rows and time.monotonic() < deadline:
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
    p.add_argument("--batch", type=int, default=10_000)
    args = p.parse_args()

    gen_dataset(args.rows, args.shards)
    sh(COMPOSE + ["build", "pathway"])
    sh(COMPOSE + ["up", "-d", "--wait", "mysql"])

    results = []
    try:
        for w in args.workers:
            runs = [run_measured(args.rows, args.batch, w) for _ in range(args.reps)]
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
