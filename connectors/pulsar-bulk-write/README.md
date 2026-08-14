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
```

The compose file pins the Pulsar standalone broker and the Pathway container
to disjoint CPU sets (see `docker-compose/variables.env`; adjust to your
topology). The dataset (20 M rows, ≈0.9 GB of CSV across 64 shards) is
generated on first use by `../datasets-shared/bulk-gen.py`.

## Results

Preliminary numbers from a shared development machine (they will be re-run on
a dedicated box before publication). Dual-socket AMD EPYC 7402 (2×24 cores,
SMT on), one socket used: the broker pinned to 12 physical cores (0-11 + SMT
siblings), the Pathway engine to the other 12 physical cores of the same
socket (12-23 + SMT siblings). Pulsar 4.0.4 standalone at stock configuration,
NVMe-backed storage. 20,000,000 rows (≈0.9 GB of CSV), median of 3 runs, every
run verified to commit exactly 20 M messages.

| Pathway workers | End-to-end time | Throughput | Speedup |
|---|---|---|---|
| 1 | 95.7 s | ≈ 209,000 rows/s | 1.00× |
| 2 | 69.3 s | ≈ 288,800 rows/s | 1.38× |
| 4 | 37.1 s | ≈ 539,100 rows/s | 2.58× |
| 8 | 28.0 s | ≈ 715,300 rows/s | 3.42× |

Throughput grows monotonically across the whole 1→2→4→8 sweep. For scale: the
same dataset through the same CSV reader into a null sink runs at ≈535,000
rows/s on one worker, so a single worker spends roughly 40% of its time on the
read-plus-parse side and the rest in the publish path.
