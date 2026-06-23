"""ClickHouse bulk-write benchmark — Pathway side.

Reads the generated CSV shard directory (``mode="static"``) and writes every row
to ClickHouse over the native protocol, timing the end-to-end ``pw.run()``. The
number of Pathway workers is ``PATHWAY_THREADS``; the sharded input lets the
filesystem reader parallelize the read across workers (each shard is owned by one
worker, chosen by a stable hash of its path), and the rows are then written to
ClickHouse in parallel.
"""

import os
import time

import pathway as pw

ROWS = int(os.environ["DATASET_SIZE"])
CLICKHOUSE_CONNECTION_STRING = os.environ.get(
    "CLICKHOUSE_CONNECTION_STRING",
    "tcp://pathway:pathway@clickhouse:9000/default",
)
CLICKHOUSE_TABLE = os.environ.get("CLICKHOUSE_TABLE", "bench_out")
BATCH = int(os.environ.get("BATCH_SIZE", "100000"))


class InputSchema(pw.Schema):
    k: int
    name: str
    value: float
    flag: bool


def main() -> None:
    table = pw.io.csv.read(f"/data/input_{ROWS}", schema=InputSchema, mode="static")
    pw.io.clickhouse.write(
        table,
        connection_string=CLICKHOUSE_CONNECTION_STRING,
        table_name=CLICKHOUSE_TABLE,
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
