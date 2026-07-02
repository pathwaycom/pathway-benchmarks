"""RabbitMQ bulk-write benchmark — Pathway side.

Reads the generated CSV shard directory (``mode="static"``) and writes every row
to a RabbitMQ **stream** with ``pw.io.rabbitmq.write`` (one JSON message per row,
over the RabbitMQ Stream protocol), timing the end-to-end ``pw.run()``. The number
of Pathway workers is ``PATHWAY_THREADS``; the sharded input lets the filesystem
reader parallelize the read across workers (each shard is owned by one worker,
chosen by a stable hash of its path), and the rows are then published in parallel.

The target stream must already exist; the run script creates it via the
management API before each run.
"""

import os
import time

import pathway as pw

ROWS = int(os.environ["DATASET_SIZE"])
DATASET_PATH = os.environ.get("DATASET_PATH", f"/data/input_{ROWS}")
RABBITMQ_URI = os.environ.get(
    "RABBITMQ_URI", "rabbitmq-stream://guest:guest@rabbitmq:5552"
)
RABBITMQ_STREAM = os.environ.get("RABBITMQ_STREAM", "bench_out")


class InputSchema(pw.Schema):
    k: int
    name: str
    value: float
    flag: bool


def main() -> None:
    table = pw.io.csv.read(DATASET_PATH, schema=InputSchema, mode="static")
    pw.io.rabbitmq.write(
        table,
        RABBITMQ_URI,
        RABBITMQ_STREAM,
        format="json",
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
