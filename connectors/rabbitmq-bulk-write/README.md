# RabbitMQ Bulk-Write Benchmark

Measures how fast the Pathway Live Data Framework writes a dataset into a
**RabbitMQ stream** with `pw.io.rabbitmq.write`, end-to-end, and how it scales with
the number of Pathway workers. Rows are read from a directory of **CSV shards** and
published as **one JSON message per row** over the RabbitMQ **Stream** protocol.

This is the QuestDB/PostgreSQL bulk-write benchmark with the sink swapped for
RabbitMQ Streams: the **same dataset schema**, the **same core pinning**, the
**same end-to-end timing**, and an out-of-band exact-count verification (see
*Methodology*). Like those
benchmarks it uses the **parallelized filesystem reader**, so the worker sweep
scales the read; each worker publishes in parallel.

Two containers wired by `docker-compose`: **RabbitMQ** (with the `rabbitmq_stream`
plugin, the same image/setup the Pathway integration tests use) and **Pathway**.

> **This is not a RabbitMQ benchmark.** Every number reflects **Pathway + the
> input source + RabbitMQ together**, out of the box.

## Dataset size

A calibration probe (0.2 M rows, 1 worker) measured **≈ 177 000 rows/s**, putting a
20 M-row single-worker run around ~2 minutes — under the suite's 10-minute
threshold. This benchmark therefore uses the full **20 000 000 rows** (≈ 0.93 GB of
CSV, ≈ 46.7 bytes/row), the same as the other fast sinks, so the numbers are
directly comparable. RabbitMQ streams persist to disk, so this is a durable publish
rate.

## Layout

```
rabbitmq-bulk-write/
├── docker-compose/
│   ├── docker-compose.yml                 # rabbitmq (streams) + pathway
│   └── variables.env                      # dataset size, core pinning, mgmt port
├── services/pathway-all/
│   ├── Dockerfile                         # installs the latest Pathway nightly + main.py
│   └── main.py                            # read CSV shards -> rabbitmq.write, time pw.run()
└── run_rabbitmq_bulk_write.py             # generate, run per worker count, report
```

The dataset is generated once into `../datasets-shared/` and shared by all the
connector benchmarks that use the `k, name, value, flag` schema.

## License

`pw.io.rabbitmq.write` is a licensed feature — set `PATHWAY_LICENSE_KEY` before
running (the benchmark image forwards it into the container).

## Methodology

* **Dataset.** `k`, `name` (`"item_<k>"`), `value`, `flag`, in 64 CSV shards,
  mounted read-only.
* **Measured run.** `pw.io.csv.read(mode="static")`, then `pw.io.rabbitmq.write`
  (`format="json"`) to a stream recreated before each run via the management API.
  The reported number is the wall-clock of `pw.run()`, end-to-end.
* **Worker count = `PATHWAY_THREADS`.** Sharded read across workers; each worker
  publishes in parallel.
* **Repetition + median.** Each worker count is run `--reps` times (default 3); the
  **median** is reported.
* **Speed *and* count verification.** The stream is recreated before each run and
  the committed message count is read back from the management HTTP API; the count
  must equal the row count. Over a fresh stream this catches any missing or
  duplicated messages, but — unlike the database benchmarks in this suite — the
  message payloads are not inspected. Verification is never inside the timed
  window.

## Machine specs

Single-socket **AMD Ryzen 9 5900X** (Zen 3, 12 cores / 24 threads, **one NUMA
node**), 125 GiB RAM, NVMe SSD. Two CCDs of 6 cores each, each with a private
32 MiB L3. RabbitMQ is pinned to CCD 0 (`0-5,12-17`) and the Pathway engine to
CCD 1 (`6-11,18-23`) — identical placement to the QuestDB/PostgreSQL benchmarks.

## Results

End-to-end wall-clock to read the 20 M-row, 64-shard CSV dataset and publish every
row to a RabbitMQ stream, swept over 1/2/4/8 Pathway workers (median of 3 runs).
"Source bytes/s" is the input CSV byte rate (rows/s × ≈ 46.7 B/row).

| Pathway workers | End-to-end time | Throughput | Source bytes/s | Speedup |
|---:|---:|---:|---:|---:|
| 1 | 41.7 s | ≈ 479 400 rows/s | ≈ 22.4 MB/s | 1.00× |
| 2 | 35.3 s | ≈ 566 700 rows/s | ≈ 26.5 MB/s | 1.18× |
| 4 | 21.5 s | ≈ 930 700 rows/s | ≈ 43.5 MB/s | 1.94× |
| 8 | 19.8 s | ≈ 1 010 600 rows/s | ≈ 47.2 MB/s | 2.11× |

Every run committed exactly the expected number of messages (`ok=True`; the
verification is an exact count over a fresh stream — payload contents are not
inspected). RabbitMQ Streams persist to disk, so this is a durable publish rate.
Throughput scales monotonically across the whole sweep, reaching **~1 010 000
rows/s at 8 workers** (2.11×), the fastest point measured.

## Reproducing

From this directory:

```bash
python run_rabbitmq_bulk_write.py                          # workers 1 2 4 8
python run_rabbitmq_bulk_write.py --workers 8 --reps 1     # quick single check
python run_rabbitmq_bulk_write.py --rows 200000 --workers 1 --reps 1   # calibration probe
```
