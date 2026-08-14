# Pulsar bulk-read benchmark

Cold-start (backlog-drain) throughput of `pw.io.pulsar.read`. The connector
has two reading mechanisms, and this benchmark covers both:

- **Shared subscription** (the default for a plain streaming read): the
  benchmark topic is prefilled with JSON messages once, then each measured
  run attaches a fresh shared subscription positioned at the earliest message
  and streams the whole backlog through Pathway into a null sink. All the
  Pathway workers join the same shared subscription, so the broker
  distributes the topic between them and the read parallelizes across
  workers — even on a non-partitioned topic.
- **Partition-reader mode** (`subscription_type="reader"`, the Kafka-like
  mechanism and the only one compatible with persistence): every partition of
  a partitioned topic is an independent log consumed by its own non-durable
  exclusive consumer, the partitions are distributed between the Pathway
  workers, and the read positions live on the Pathway side instead of a
  broker-side subscription cursor. See the dedicated section below.

Both variants exercise the exact code path a production streaming pipeline
uses, which makes this both the cold-start and the steady-state read path
(streaming reads use the identical consumer code; the only difference is that
a live stream waits for new data instead of finishing the backlog).

A streaming read never terminates on its own, so the run script measures the
interval from the `T0` printed by the pipeline right before `pw.run()` to the
moment the subscription's `msgBacklog` reaches zero (admin API), then stops
the container. A `retention-holder` subscription created before the prefill
pins the backlog, so every run sees the identical message set.

## Running

```bash
# Shared subscription, non-partitioned topic:
python run_pulsar_bulk_read.py                       # workers 1 2 4 8, 3 reps
python run_pulsar_bulk_read.py --workers 8 --reps 1  # quick check

# Partition-reader mode, 8-partition topic, with and without persistence:
python run_pulsar_reader_read.py
python run_pulsar_reader_read.py --workers 8 --reps 1  # quick check
```

The compose file pins the Pulsar standalone broker and the Pathway container
to disjoint CPU sets (see `docker-compose/variables.env`; adjust to your
topology). The dataset used for the prefill (20 M rows) is generated on first
use by `../datasets-shared/bulk-gen.py`.

## Machine specs

Single-socket **AMD Ryzen 9 5900X** (Zen 3, 12 cores / 24 threads, **one NUMA
node**), 125 GiB RAM, NVMe SSD. Two CCDs of 6 cores each, each with a private
32 MiB L3. The Pulsar broker is pinned to CCD 0 (`0-5,12-17`) and the Pathway
engine to CCD 1 (`6-11,18-23`) — identical placement to the QuestDB /
PostgreSQL / RabbitMQ benchmarks, so each service owns a private L3 and they
never share a physical core.

## Results — shared subscription, non-partitioned topic

Pathway 0.32.2.dev941 (nightly), Pulsar 4.0.4 standalone at stock
configuration, NVMe-backed storage. 20,000,000 prefilled messages in a
non-partitioned topic, median of 3 runs; the machine was otherwise idle for
every measured run.

| Pathway workers | Backlog drain time | Throughput | Speedup |
|---|---|---|---|
| 1 | 119.8 s | ≈ 167,000 rows/s | 1.00× |
| 2 | 66.4 s | ≈ 301,200 rows/s | 1.80× |
| 4 | 42.8 s | ≈ 466,900 rows/s | 2.80× |
| 8 | 35.9 s | ≈ 557,300 rows/s | 3.34× |

Run-to-run spread was below 1% at every worker count. Throughput grows
monotonically across the whole 1→2→4→8 sweep and near-linearly up to 4
workers: the broker distributes the shared subscription between the
per-worker consumers, so adding workers directly adds read capacity. The 8
worker point runs 8 workers on the 6 physical cores of the engine's CCD (plus
SMT), so the last doubling is bounded by cores rather than by the connector.

The single-worker read rate is lower than the single-worker write rate
(≈167k vs ≈308k rows/s); this is the per-message acknowledgement cost
inherent to the shared-subscription mechanism — see the next section for the
explanation and for the reader-mode numbers that avoid it.

## Results — reader mode, partitioned topic

The same benchmark, same machine and same 20 M rows (run by
`run_pulsar_reader_read.py`), but the topic is created with **8 partitions**
(so it divides evenly across every measured worker count;
`pw.io.pulsar.write` publishes to a partitioned topic transparently) and the
read uses `subscription_type="reader"`. The reader mode leaves no
broker-side subscription whose backlog could be polled, so completion is
detected by an in-graph row counter (`reduce` + `pw.io.subscribe`) that also
verifies correctness: every run must count **exactly** 20,000,000 rows, which
catches both losses and duplicates. Note that this counter is extra work the
shared-subscription runs above do not perform — the reader-mode numbers below
carry slightly *more* per-row engine work, and win regardless.

Without persistence:

| Pathway workers | Backlog drain time | Throughput | Speedup |
|---|---|---|---|
| 1 | 29.1 s | ≈ 688,100 rows/s | 1.00× |
| 2 | 16.1 s | ≈ 1,245,600 rows/s | 1.81× |
| 4 | 10.7 s | ≈ 1,877,100 rows/s | 2.73× |
| 8 | 10.1 s | ≈ 1,986,100 rows/s | 2.89× |

With persistence enabled (filesystem backend, fresh state per run — the
configuration in which the reader mode recovers from a restart without losing
or duplicating messages):

| Pathway workers | Backlog drain time | Throughput | Speedup |
|---|---|---|---|
| 1 | 29.1 s | ≈ 688,100 rows/s | 1.00× |
| 2 | 15.9 s | ≈ 1,260,900 rows/s | 1.83× |
| 4 | 13.3 s | ≈ 1,507,800 rows/s | 2.19× |
| 8 | 11.8 s | ≈ 1,693,200 rows/s | 2.46× |

All 24 runs delivered exactly 20 M rows; run-to-run spread stayed within a
few percent. Persistence is free at 1–2 workers and costs ~15–20% at 4–8,
where the drain takes only ~10 s and the fixed snapshotting overhead becomes
visible against it.

### Why the reader mode is ~4× faster per worker

The gap (≈167k vs ≈688k rows/s on one worker) is acknowledgement traffic, a
consequence of how the two mechanisms track progress in the Pulsar protocol:

- In a **shared subscription**, the broker owns the delivery state. Every
  delivered message must be acknowledged **individually** (the Shared subtype
  forbids cumulative acks), because the acks are what advances the durable
  cursor, lets the broker trim the backlog, and feeds its flow control — a
  consumer that stops acking is cut off from dispatch after
  `maxUnackedMessagesPerConsumer` (50,000 by default) outstanding messages.
  So at high rates the consumer sends one acknowledgement per message, and in
  the current Rust client (`pulsar-rs`) those acks are processed on the same
  event loop that delivers incoming messages: delivery and acknowledgement
  compete for the same thread. The protocol itself allows batching many
  message ids into one ack command (the Java client groups acks with
  `acknowledgmentGroupTime`), so this cost is a client-library property
  rather than a broker limit — and it parallelizes away as workers are
  added, which is why the shared-subscription sweep still scales cleanly.
- In the **reader mode** there are no acknowledgements at all: each partition
  is read by a non-durable exclusive consumer, and the positions of the
  delivered messages *are* the connector's offsets, tracked on the Pathway
  side (and snapshotted by persistence, which is what makes lossless,
  duplicate-free restart recovery possible). Removing the per-message ack
  path frees the whole delivery loop, hence ≈4× per-worker throughput and
  ≈2 M rows/s at 8 workers, where the broker's own dispatch on its CCD
  becomes the next limit.

The trade-off is operational rather than raw speed: the shared subscription
keeps progress on the broker (visible to standard Pulsar tooling, resumable
by subscription name, backlog managed by the broker), while the reader mode
keeps progress in Pathway's persistence layer and requires a partitioned
topic to parallelize.
