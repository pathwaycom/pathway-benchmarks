"""Pulsar bulk-read benchmark — Pathway side, partition-reader mode.

Streams the prefilled partitioned topic through ``pw.io.pulsar.read`` in the
Kafka-like partition-reader mode (``subscription_type="reader"``) into a null
sink, with an in-graph row counter subscribed on the side. ``T0`` is printed
right before ``pw.run()``; every time the counter reaches (or exceeds) the
expected row count, ``T1=<unix seconds> CNT=<rows>`` is printed, so the run
script can compute the exact drain time and verify that exactly the expected
number of rows was delivered (an overshoot would indicate duplicates).

``PERSISTENCE=1`` enables filesystem persistence inside the container. The
state is fresh for every run, since each measured run uses a new container.
"""

import os
from time import time as now

import pathway as pw

ROWS = int(os.environ["DATASET_SIZE"])
PULSAR_URI = os.environ.get("PULSAR_URI", "pulsar://pulsar:6650")
PULSAR_TOPIC = os.environ.get("PULSAR_TOPIC", "bench_in_p8")
PERSISTENCE = os.environ.get("PERSISTENCE", "0") == "1"


def main() -> None:
    table = pw.io.pulsar.read(
        PULSAR_URI,
        PULSAR_TOPIC,
        format="raw",
        mode="streaming",
        subscription_type="reader",
        start_from="beginning",
        autocommit_duration_ms=100,
        name="bench_reader",
    )
    pw.io.null.write(table)

    counts = table.reduce(cnt=pw.reducers.count())

    def on_change(key, row, time, is_addition):
        if is_addition and row["cnt"] >= ROWS:
            print(f"T1={now():.3f} CNT={row['cnt']}", flush=True)

    pw.io.subscribe(counts, on_change=on_change)

    kwargs = {}
    if PERSISTENCE:
        backend = pw.persistence.Backend.filesystem("/pstorage")
        kwargs["persistence_config"] = pw.persistence.Config(backend)

    print(f"T0={now():.3f}", flush=True)
    pw.run(monitoring_level=pw.MonitoringLevel.NONE, **kwargs)


if __name__ == "__main__":
    main()
