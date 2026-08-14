"""Pulsar bulk-read benchmark — topic prefill.

Reads the generated CSV shard directory (``mode="static"``) and publishes
every row to the benchmark topic as one JSON message. Run once before the
measured read runs; the run script creates a retention-holder subscription
beforehand so that the prefilled backlog is not deleted between runs.
"""

import os

import pathway as pw

ROWS = int(os.environ["DATASET_SIZE"])
DATASET_PATH = os.environ.get("DATASET_PATH", f"/data/input_{ROWS}")
PULSAR_URI = os.environ.get("PULSAR_URI", "pulsar://pulsar:6650")
PULSAR_TOPIC = os.environ.get("PULSAR_TOPIC", "bench_in")


class InputSchema(pw.Schema):
    k: int
    name: str
    value: float
    flag: bool


def main() -> None:
    table = pw.io.csv.read(DATASET_PATH, schema=InputSchema, mode="static")
    pw.io.pulsar.write(table, PULSAR_URI, PULSAR_TOPIC, format="json")
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)
    print("FILL_DONE")


if __name__ == "__main__":
    main()
