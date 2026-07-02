"""SQLite bulk-write benchmark — Pathway side.

Reads the generated CSV shard directory (``mode="static"``) and writes every row
to a SQLite database file with ``pw.io.sqlite.write``, timing the end-to-end
``pw.run()``. The number of Pathway workers is ``PATHWAY_THREADS``; the sharded
input lets the filesystem reader parallelize the read across workers (each shard
is owned by one worker, chosen by a stable hash of its path).

Note: SQLite is an *embedded, single-writer* database — a single file guarded by
a database-level write lock. There is no server process and no per-CCD pinning of
a separate service; the whole pipeline (read + parse + write) runs in the Pathway
container. The output file lives on a bind-mounted directory so it can be
verified out-of-band after the run.
"""

import os
import time

import pathway as pw

ROWS = int(os.environ["DATASET_SIZE"])
BATCH = int(os.environ.get("BATCH_SIZE", "10000"))
DATASET_PATH = os.environ.get("DATASET_PATH", f"/data/input_{ROWS}")
SQLITE_PATH = os.environ.get("SQLITE_PATH", "/out/bench.db")
SQLITE_TABLE = os.environ.get("SQLITE_TABLE", "bench_out")


class InputSchema(pw.Schema):
    k: int
    name: str
    value: float
    flag: bool


def main() -> None:
    table = pw.io.csv.read(DATASET_PATH, schema=InputSchema, mode="static")
    pw.io.sqlite.write(
        table,
        SQLITE_PATH,
        SQLITE_TABLE,
        init_mode="replace",
        max_batch_size=BATCH,
    )

    start = time.perf_counter()
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)
    elapsed = time.perf_counter() - start

    print(f"WORKERS={os.environ.get('PATHWAY_THREADS', '1')}")
    print(f"ROWS={ROWS}")
    print(f"ELAPSED_SECONDS={elapsed:.2f}")
    print(f"ROWS_PER_SECOND={ROWS / elapsed:.0f}")


if __name__ == "__main__":
    main()
