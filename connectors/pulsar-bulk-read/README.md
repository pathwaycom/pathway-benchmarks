# Pulsar bulk-read benchmark

Cold-start (backlog-drain) throughput of `pw.io.pulsar.read`: the benchmark
topic is prefilled with JSON messages once, then each measured run attaches a
fresh shared subscription positioned at the earliest message and streams the
whole backlog through Pathway into a null sink. All the Pathway workers join
the same shared subscription, so the broker distributes the topic between them
and the read parallelizes across workers — the same mechanism a production
streaming pipeline uses, which makes this both the cold-start and the
steady-state read path (streaming reads use the identical consumer code; the
only difference is that a live stream waits for new data instead of finishing
the backlog).

A streaming read never terminates on its own, so the run script measures the
interval from the `T0` printed by the pipeline right before `pw.run()` to the
moment the subscription's `msgBacklog` reaches zero (admin API), then stops
the container. A `retention-holder` subscription created before the prefill
pins the backlog, so every run sees the identical message set.

## Running

```bash
python run_pulsar_bulk_read.py                       # workers 1 2 4 8, 3 reps
python run_pulsar_bulk_read.py --workers 8 --reps 1  # quick check
```

The compose file pins the Pulsar standalone broker and the Pathway container
to disjoint CPU sets (see `docker-compose/variables.env`; adjust to your
topology). The dataset used for the prefill (20 M rows) is generated on first
use by `../datasets-shared/bulk-gen.py`.

## Results

Preliminary numbers from a shared development machine (they will be re-run on
a dedicated box before publication). Dual-socket AMD EPYC 7402 (2×24 cores,
SMT on), one socket used: the broker pinned to 12 physical cores (0-11 + SMT
siblings), the Pathway engine to the other 12 physical cores of the same
socket (12-23 + SMT siblings). Pulsar 4.0.4 standalone at stock configuration,
NVMe-backed storage. 20,000,000 prefilled messages, median of 3 runs.

| Pathway workers | Backlog drain time | Throughput | Speedup |
|---|---|---|---|
| 1 | 250.7 s | ≈ 79,800 rows/s | 1.00× |
| 2 | 138.9 s | ≈ 144,000 rows/s | 1.81× |
| 4 | 75.8 s | ≈ 264,000 rows/s | 3.31× |
| 8 | 48.8 s | ≈ 409,800 rows/s | 5.14× |

Throughput grows monotonically and near-linearly across the whole 1→2→4→8
sweep: the broker distributes the shared subscription between the per-worker
consumers, so adding workers directly adds read capacity.

**Known bottleneck.** The single-worker read rate is noticeably lower than the
single-worker write rate (≈80k vs ≈209k rows/s), and it is a property of the
client library's delivery pipeline, not of the Pathway-side read loop. The
reader thread sits at ~50% CPU; batching the reader's runtime entries (one
`block_on` drains up to 1000 locally queued messages) gained only ~7%, and
deepening the consumer's receiver queue to 50k changed nothing. The limiting
path is `pulsar-rs`'s `ConsumerEngine`: it sends one `CommandAck` per message
and processes those acks in the same event loop that delivers incoming
messages, so every delivered message competes with its own acknowledgement.
The protocol and `send_ack` already accept batches of message ids; teaching
the client to group acknowledgements (like the Java client's
`acknowledgmentGroupTime`) is the proper upstream fix.
