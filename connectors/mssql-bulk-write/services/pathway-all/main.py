"""MS SQL Server bulk-write benchmark — Pathway side.

Reads the generated CSV shard directory (``mode="static"``) and writes every row
to SQL Server with ``pw.io.mssql.write``, timing the end-to-end ``pw.run()``. The
number of Pathway workers is ``PATHWAY_THREADS``; the sharded input lets the
filesystem reader parallelize the read across workers (each shard is owned by one
worker, chosen by a stable hash of its path), and the rows are then written to
SQL Server in parallel (each worker drives its own connection / batched INSERT statements).
"""

import os
import time

import pathway as pw

ROWS = int(os.environ["DATASET_SIZE"])
BATCH = int(os.environ.get("BATCH_SIZE", "10000"))
DATASET_PATH = os.environ.get("DATASET_PATH", f"/data/input_{ROWS}")
MSSQL_CONNECTION_STRING = os.environ.get(
    "MSSQL_CONNECTION_STRING",
    "Server=tcp:mssql,1433;Database=testdb;User Id=sa;"
    "Password=YourStrong!Passw0rd;TrustServerCertificate=true",
)
MSSQL_TABLE = os.environ.get("MSSQL_TABLE", "bench_out")


class InputSchema(pw.Schema):
    k: int
    name: str
    value: float
    flag: bool


def main() -> None:
    table = pw.io.csv.read(DATASET_PATH, schema=InputSchema, mode="static")
    pw.io.mssql.write(
        table,
        MSSQL_CONNECTION_STRING,
        MSSQL_TABLE,
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
