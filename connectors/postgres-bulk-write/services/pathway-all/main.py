"""Postgres bulk-write benchmark — Pathway side.

Reads the generated CSV shard directory (``mode="static"``) and writes every row
to PostgreSQL with ``pw.io.postgres.write`` (the output connector streams each
batch in over the database's binary ``COPY`` protocol), timing the end-to-end
``pw.run()``. The number of Pathway workers is ``PATHWAY_THREADS``; the sharded
input lets the filesystem reader parallelize the read across workers (each shard
is owned by one worker, chosen by a stable hash of its path), and the rows are
then written to PostgreSQL in parallel.
"""

import os
import time

import pathway as pw

ROWS = int(os.environ["DATASET_SIZE"])
BATCH = int(os.environ.get("BATCH_SIZE", "10000"))
DATASET_PATH = os.environ.get("DATASET_PATH", f"/data/input_{ROWS}")

POSTGRES_SETTINGS = {
    "host": os.environ.get("PGHOST", "postgres"),
    "port": os.environ.get("PGPORT", "5432"),
    "dbname": os.environ.get("PGDATABASE", "bench"),
    "user": os.environ.get("PGUSER", "bench"),
    "password": os.environ.get("PGPASSWORD", "bench"),
}


class InputSchema(pw.Schema):
    k: int
    name: str
    value: float
    flag: bool


def main() -> None:
    table = pw.io.csv.read(DATASET_PATH, schema=InputSchema, mode="static")
    pw.io.postgres.write(
        table,
        POSTGRES_SETTINGS,
        "bench_out",
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
