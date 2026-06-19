"""QuestDB bulk-write benchmark — Pathway side.

Reads the generated CSV shard directory (``mode="static"``) and writes every row
to QuestDB over the InfluxDB Line Protocol, timing the end-to-end ``pw.run()``.
The number of Pathway workers is ``PATHWAY_THREADS``; the sharded input lets the
filesystem reader parallelize the read across workers.
"""

import os
import time

import pathway as pw

ROWS = int(os.environ["DATASET_SIZE"])
QUESTDB_CONNECTION_STRING = os.environ.get(
    "QUESTDB_CONNECTION_STRING", "http::addr=questdb:9000;"
)
QUESTDB_TABLE = os.environ.get("QUESTDB_TABLE", "bench_out")


class InputSchema(pw.Schema):
    k: int
    name: str
    value: float
    flag: bool


def main() -> None:
    table = pw.io.csv.read(f"/data/input_{ROWS}", schema=InputSchema, mode="static")
    pw.io.questdb.write(
        table,
        connection_string=QUESTDB_CONNECTION_STRING,
        table_name=QUESTDB_TABLE,
        designated_timestamp_policy="use_now",
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
