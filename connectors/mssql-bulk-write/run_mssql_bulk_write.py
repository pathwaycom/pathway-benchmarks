"""Run the MS SQL Server bulk-write benchmark across Pathway worker counts.

Two services plus an init container (SQL Server + a one-shot database creator +
Pathway). The dataset is generated as CSV shards; each measured run reads the
shard directory (bounded, ``mode="static"``) and writes every row to SQL Server
with ``pw.io.mssql.write`` (batched INSERT statements). The sharded input lets the
filesystem reader parallelize the read across workers (each shard is owned by
exactly one worker, chosen by a stable hash of its path), so the worker sweep
exercises both the parallel read and the parallel write. For each worker count
the run is repeated ``--reps`` times and the median is reported.

This benchmark is deliberately the QuestDB/PostgreSQL bulk-write benchmark with
the database swapped for SQL Server: same dataset, same core pinning, same
end-to-end timing and out-of-band correctness verification.

Usage:
    python run_mssql_bulk_write.py                       # workers 1 2 4 8
    python run_mssql_bulk_write.py --workers 8 --reps 1  # quick check
    python run_mssql_bulk_write.py --rows 200000 --workers 1 --reps 1  # calibration probe
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

PROJECT = (os.environ.get("USER", "mssqlbulk") + "_mssqlbulk").replace(".", "_")
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
SA_PASSWORD = "YourStrong!Passw0rd"


def sh(cmd, **kw):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    return subprocess.run(cmd, **kw)


def sqlcmd(sql: str) -> str:
    """Run a T-SQL statement inside the SQL Server container and return the raw
    pipe-separated output. Used only for setup/verification, never inside the
    timed window."""
    res = subprocess.run(
        COMPOSE
        + [
            "exec",
            "-T",
            "mssql",
            "/opt/mssql-tools18/bin/sqlcmd",
            "-S",
            "localhost",
            "-U",
            "sa",
            "-P",
            SA_PASSWORD,
            "-No",
            "-d",
            "testdb",
            "-h",
            "-1",
            "-W",
            "-s",
            "|",
            "-Q",
            "SET NOCOUNT ON; " + sql,
        ],
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


def last_data_line(out: str) -> str:
    for line in reversed(out.splitlines()):
        line = line.strip()
        if line and not set(line) <= set("-| "):
            return line
    return ""


def mssql_count() -> int:
    out = sqlcmd(f"SELECT count(*) FROM {TABLE}")
    try:
        return int(last_data_line(out))
    except ValueError:
        return -1


def verify_correctness(rows: int) -> tuple[bool, dict]:
    """Check, over the SQL Server wire protocol, that every row landed intact.

    Runs *after* the measured run, so it is never part of the timed window. The
    generated data has ``k`` = 0..rows-1 and ``name`` = "item_<k>", which makes a
    handful of aggregates a strong end-to-end integrity check: exact row count,
    the key range and sum (catches missing/duplicate/garbled keys), the derived
    ``name`` column, the absence of nulls, and — specific to the stream-of-changes
    format ``pw.io.mssql.write`` appends — that every row is an insertion
    (``diff = 1``), so ``sum(diff)`` must equal the row count.
    """
    expected_sum = rows * (rows - 1) // 2
    out = sqlcmd(
        f"SELECT count(*), ISNULL(MIN(k),-1), ISNULL(MAX(k),-1), "
        f"ISNULL(SUM(CAST(k AS BIGINT)),0), ISNULL(SUM(CAST([diff] AS BIGINT)),0), "
        f"SUM(CASE WHEN name <> CONCAT('item_', CAST(k AS VARCHAR(20))) THEN 1 ELSE 0 END), "
        f"SUM(CASE WHEN value IS NULL OR flag IS NULL OR name IS NULL THEN 1 ELSE 0 END) "
        f"FROM {TABLE}"
    )
    fields = [int(x) for x in last_data_line(out).split("|")]
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
    sqlcmd(f"IF OBJECT_ID('{TABLE}','U') IS NOT NULL DROP TABLE {TABLE}")
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
    deadline = time.monotonic() + 120
    while mssql_count() < rows and time.monotonic() < deadline:
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
    sh(COMPOSE + ["up", "-d", "--wait", "mssql"])
    sh(COMPOSE + ["up", "--no-deps", "mssql-init"])

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
