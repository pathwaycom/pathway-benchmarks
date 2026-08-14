"""Pulsar bulk-write benchmark — Pathway side.

Reads the generated CSV shard directory (``mode="static"``) and writes every
row to an Apache Pulsar topic with ``pw.io.pulsar.write`` (one JSON message per
row), timing the end-to-end ``pw.run()``. The number of Pathway workers is
``PATHWAY_THREADS``; the sharded input lets the filesystem reader parallelize
the read across workers (each shard is owned by one worker, chosen by a stable
hash of its path), and the rows are then published in parallel.

The target topic is (re)created by the run script via the admin API before
each run.
"""

import os
import time

import pathway as pw

ROWS = int(os.environ["DATASET_SIZE"])
DATASET_PATH = os.environ.get("DATASET_PATH", f"/data/input_{ROWS}")
PULSAR_URI = os.environ.get("PULSAR_URI", "pulsar://pulsar:6650")
PULSAR_TOPIC = os.environ.get("PULSAR_TOPIC", "bench_out")


class InputSchema(pw.Schema):
    k: int
    name: str
    value: float
    flag: bool


def main() -> None:
    table = pw.io.csv.read(DATASET_PATH, schema=InputSchema, mode="static")
    pw.io.pulsar.write(
        table,
        PULSAR_URI,
        PULSAR_TOPIC,
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
