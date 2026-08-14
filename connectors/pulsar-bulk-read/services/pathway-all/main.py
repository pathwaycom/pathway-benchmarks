"""Pulsar bulk-read benchmark — Pathway side.

Streams the prefilled benchmark topic through ``pw.io.pulsar.read`` into a
null sink. All the Pathway workers attach to one shared subscription, so the
read parallelizes across them. A streaming read never finishes on its own;
the run script watches the subscription backlog over the admin API, records
the completion time when the backlog reaches zero, and stops the container.

``T0=<unix seconds>`` is printed right before ``pw.run()`` so that the run
script can subtract the container and interpreter startup from the elapsed
time.
"""

import os
import time

import pathway as pw

PULSAR_URI = os.environ.get("PULSAR_URI", "pulsar://pulsar:6650")
PULSAR_TOPIC = os.environ.get("PULSAR_TOPIC", "bench_in")
SUBSCRIPTION = os.environ["PULSAR_SUBSCRIPTION"]


def main() -> None:
    table = pw.io.pulsar.read(
        PULSAR_URI,
        PULSAR_TOPIC,
        format="raw",
        mode="streaming",
        subscription_name=SUBSCRIPTION,
        autocommit_duration_ms=100,
    )
    pw.io.null.write(table)

    print(f"T0={time.time():.3f}", flush=True)
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)


if __name__ == "__main__":
    main()
