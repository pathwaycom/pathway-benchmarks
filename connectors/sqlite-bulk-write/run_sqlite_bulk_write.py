"""Run the SQLite bulk-write benchmark across Pathway worker counts.

One container (Pathway only — SQLite is embedded). The dataset is generated as
CSV shards; each measured run reads the shard directory (bounded,
``mode="static"``) and writes every row to a SQLite database file with
``pw.io.sqlite.write``. The sharded input lets the filesystem reader parallelize
the *read* across workers, but SQLite is a single-writer database: a file guarded
by a database-level write lock. For each worker count the run is repeated
``--reps`` times and the median is reported.

This benchmark is deliberately the QuestDB/PostgreSQL bulk-write benchmark with
the database swapped for SQLite: same dataset, same end-to-end timing and
out-of-band correctness verification. Because SQLite is single-writer, the worker
sweep is expected to *not* scale the write (it may even regress or fail under
lock contention beyond one writer) — that contrast is part of what this benchmark
shows.

Usage:
    python run_sqlite_bulk_write.py                       # workers 1 2 4 8
    python run_sqlite_bulk_write.py --workers 1 --reps 1  # quick check
    python run_sqlite_bulk_write.py --rows 200000 --workers 1 --reps 1  # calibration probe
"""

import argparse
import os
import re
import sqlite3
import statistics
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

SHARED_DATASETS = os.path.join(ROOT, "..", "datasets-shared")
GEN = os.path.join(SHARED_DATASETS, "bulk-gen.py")
OUT_DB = os.path.join(ROOT, "out", "bench.db")

PROJECT = (os.environ.get("USER", "sqlitebulk") + "_sqlitebulk").replace(".", "_")
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


def verify_correctness(rows: int) -> tuple[bool, dict]:
    """Check, by reading the SQLite file directly, that every row landed intact.

    Runs *after* the measured run, so it is never part of the timed window. The
    generated data has ``k`` = 0..rows-1 and ``name`` = "item_<k>", which makes a
    handful of aggregates a strong end-to-end integrity check: exact row count,
    the key range and sum (catches missing/duplicate/garbled keys), the derived
    ``name`` column, the absence of nulls, and — specific to the stream-of-changes
    format ``pw.io.sqlite.write`` appends — that every row is an insertion
    (``diff = 1``), so ``sum(diff)`` must equal the row count.
    """
    expected_sum = rows * (rows - 1) // 2
    con = sqlite3.connect(OUT_DB)
    try:
        row = con.execute(
            f"SELECT count(*), coalesce(min(k), -1), coalesce(max(k), -1), "
            f"coalesce(sum(k), 0), coalesce(sum(diff), 0), "
            f"coalesce(sum(name <> 'item_' || k), 0), "
            f"coalesce(sum(value IS NULL OR flag IS NULL OR name IS NULL), 0) "
            f"FROM {TABLE}"
        ).fetchone()
    finally:
        con.close()
    keys = ["count", "min_k", "max_k", "sum_k", "sum_diff", "bad_name", "null_cols"]
    checks = dict(zip(keys, [int(x) for x in row]))
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


def reset_output() -> None:
    for suffix in ("", "-wal", "-shm", "-journal"):
        try:
            os.remove(OUT_DB + suffix)
        except FileNotFoundError:
            pass


def run_measured(rows: int, batch: int, workers: int) -> tuple[float | None, bool]:
    reset_output()
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
        # SQLite is single-writer; multiple concurrent writers can fail under
        # lock contention. Record the failure and keep the sweep going.
        print(f"  RUN FAILED (workers={workers}); tail:")
        print("\n".join(out.strip().splitlines()[-15:]))
        return None, False
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

    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    gen_dataset(args.rows, args.shards)
    sh(COMPOSE + ["build", "pathway"])

    results = []
    try:
        for w in args.workers:
            runs = [run_measured(args.rows, args.batch, w) for _ in range(args.reps)]
            times = [t for t, _ in runs if t is not None]
            ok = (
                bool(times)
                and all(ok for t, ok in runs if t is not None)
                and len(times) == len(runs)
            )
            median = statistics.median(times) if times else None
            results.append(
                {
                    "workers": w,
                    "median": median,
                    "rows_per_second": (args.rows / median) if median else None,
                    "ok": ok,
                    "runs": [t for t, _ in runs],
                }
            )
    finally:
        sh(COMPOSE + ["down", "-v"])
        reset_output()

    base = next((r["rows_per_second"] for r in results if r["rows_per_second"]), None)
    print(
        f"\n==================== RESULTS  ({args.rows:,} rows, "
        f"median of {args.reps}) ===================="
    )
    print(
        f"{'workers':>8}{'median_s':>11}{'rows/s':>14}{'speedup':>9}{'ok':>5}   runs(s)"
    )
    for r in results:
        if r["median"] is None:
            print(
                f"{r['workers']:>8}{'FAILED':>11}{'-':>14}{'-':>9}{str(r['ok']):>5}   (lock contention / error)"
            )
            continue
        speedup = (r["rows_per_second"] / base) if base else 1.0
        runs_str = ", ".join("FAIL" if t is None else f"{t:.1f}" for t in r["runs"])
        print(
            f"{r['workers']:>8}{r['median']:>11.2f}{r['rows_per_second']:>14,.0f}"
            f"{speedup:>8.2f}x{str(r['ok']):>5}   {runs_str}"
        )


if __name__ == "__main__":
    main()
