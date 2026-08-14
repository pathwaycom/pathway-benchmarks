# Pulsar bulk-write benchmark

End-to-end throughput of `pw.io.pulsar.write`: Pathway reads a sharded CSV
dataset (bounded, `mode="static"`), does the basic per-row processing implied
by parsing, and publishes every row to an Apache Pulsar topic as one JSON
message. The measured time is the whole `pw.run()`, so the numbers reflect
**Pathway + the input source + Pulsar together, out of the box**, not Pulsar's
standalone ingestion ceiling.

The output connector is multi-threaded: each Pathway worker owns its own
producer, and the sharded input lets the filesystem reader parallelize across
workers (each shard is owned by exactly one worker), so the worker sweep
exercises both the parallel read and the parallel publish. Correctness is
verified after every run: the topic is recreated before the run and its
`msgInCounter` must equal the number of rows.

## Running

```bash
python run_pulsar_bulk_write.py                       # workers 1 2 4 8, 3 reps
python run_pulsar_bulk_write.py --workers 8 --reps 1  # quick check
python run_pulsar_bulk_write.py --partitions 8        # 8-partition target topic
```

The compose file pins the Pulsar standalone broker and the Pathway container
to disjoint CPU sets (see `docker-compose/variables.env`; adjust to your
topology). The dataset (20 M rows, ≈0.9 GB of CSV across 64 shards) is
generated on first use by `../datasets-shared/bulk-gen.py`.

## Machine specs

Single-socket **AMD Ryzen 9 5900X** (Zen 3, 12 cores / 24 threads, **one NUMA
node**), 125 GiB RAM, NVMe SSD. Two CCDs of 6 cores each, each with a private
32 MiB L3. The Pulsar broker is pinned to CCD 0 (`0-5,12-17`) and the Pathway
engine to CCD 1 (`6-11,18-23`) — identical placement to the QuestDB /
PostgreSQL / RabbitMQ benchmarks, so each service owns a private L3 and they
never share a physical core.

## Results

Pathway 0.32.2.dev941 (nightly), Pulsar 4.0.4 standalone at stock
configuration, NVMe-backed storage. 20,000,000 rows (≈0.9 GB of CSV), median
of 3 runs, every run verified to commit exactly 20 M messages; the machine
was otherwise idle for every measured run.

| Pathway workers | End-to-end time | Throughput | Speedup |
|---|---|---|---|
| 1 | 64.9 s | ≈ 308,300 rows/s | 1.00× |
| 2 | 54.2 s | ≈ 369,300 rows/s | 1.20× |
| 4 | 39.3 s | ≈ 509,400 rows/s | 1.65× |
| 8 | 32.2 s | ≈ 622,100 rows/s | 2.02× |

Throughput grows monotonically across the whole 1→2→4→8 sweep; the 8-worker
point runs 8 workers on the 6 physical cores of the engine's CCD (plus SMT),
so the last doubling is bounded by cores rather than by the connector. For
scale: the same dataset through the same CSV reader into a null sink runs at
≈970,700 rows/s on one worker (median of 3 on the same machine), so a single
worker spends roughly a third of its time on the read-plus-parse side and the
rest in the publish path.

## Results — 8-partition topic

The same benchmark, machine, and dataset, but the target topic is created
with **8 partitions** (`python run_pulsar_bulk_write.py --partitions 8`);
keyless messages are spread across the partitions by the client, and the
correctness check reads the message count aggregated over all the
partitions. The last column compares against the non-partitioned table
above.

| Pathway workers | End-to-end time | Throughput | Speedup | vs non-partitioned |
|---|---|---|---|---|
| 1 | 68.0 s | ≈ 294,300 rows/s | 1.00× | −5% |
| 2 | 55.0 s | ≈ 363,700 rows/s | 1.24× | −2% |
| 4 | 35.5 s | ≈ 563,900 rows/s | 1.92× | +11% |
| 8 | 28.8 s | ≈ 694,000 rows/s | 2.36× | +12% |

Every run again committed exactly 20 M messages, so high-volume publishing
into partitioned topics is verified end to end.

**Why the effect is small and changes sign.** A non-partitioned Pulsar topic
is backed by a single managed ledger on the broker: every publish, from
however many producers, goes through one ordered append path. Partitioning
splits the topic into independent per-partition ledgers with parallel write
paths. Both signs in the table follow from that:

- At 1–2 workers the publish rate is nowhere near the single ledger's limit,
  so partitioning only adds client-side cost: each message is routed to one
  of 8 sub-producers, and the same message flow is split into 8 streams of
  smaller, less efficient batches (−2…−5%).
- At 4–8 workers the single ordered append path starts to be contended, and
  8 parallel ledgers relieve the broker (+11–12%, lifting the ceiling on
  this machine from ≈622k to ≈694k rows/s).

In other words, partitioning a Pulsar topic is not a publish-throughput
optimization until the publish rate approaches the single-ledger limit
(≈600k msg/s on this broker configuration). The main reason to partition is
on the consumer side: it enables the partition-reader mode measured in the
read benchmark, which is where partitions pay off dramatically.
