# MySQL Bulk-Write Benchmark

Measures how fast the Pathway Live Data Framework writes a dataset into **MySQL**
with `pw.io.mysql.write`, end-to-end, and how it scales with the number of
Pathway workers. Rows are read from a directory of **CSV shards** and written to
MySQL.

This is the QuestDB/PostgreSQL bulk-write benchmark with the database swapped for
MySQL: the **same dataset schema**, the **same core pinning**, the **same
end-to-end timing**, and the **same out-of-band correctness verification**, so the
databases are directly comparable. Like those benchmarks it uses the
**parallelized filesystem reader**, so the worker sweep scales the read; the
write path is discussed below.

Two containers wired by `docker-compose`: **MySQL** and **Pathway**.

> **This is not a MySQL benchmark.** It measures the *full cycle* — the Pathway
> engine reading the input source, doing very basic per-row processing, and
> writing to MySQL — so every number reflects **Pathway + the input source +
> MySQL together**. MySQL here is configured for write throughput (relaxed
> durability, see *Server durability and worker scaling*); it is not MySQL's
> standalone ingestion ceiling.

## Dataset size

The MySQL output connector bulk-writes each batch (multi-row `INSERT` /
`LOAD DATA LOCAL INFILE` — see *Write path and scaling*). On a throughput-configured
server (below) it lands ~190 000 rows/s at a single worker and scales past a
quarter-million with more, within range of the binary-`COPY`/native-bulk sinks in
this suite.

This benchmark uses **5 000 000 rows** (≈ 0.23 GB of CSV, ≈ 45 bytes/row).
Throughput is reported in both **rows/s** and **MB/s** so it stays directly
comparable to the 20 M-row fast benchmarks on a *rate* basis.

## Layout

```
mysql-bulk-write/
├── docker-compose/
│   ├── docker-compose.yml                 # mysql (throughput-tuned) + pathway
│   └── variables.env                      # dataset size, batch, core pinning, port
├── services/pathway-all/
│   ├── Dockerfile                         # installs the latest Pathway nightly + main.py
│   └── main.py                            # read CSV shards -> mysql.write, time pw.run()
└── run_mysql_bulk_write.py                # generate, run per worker count, report
```

The dataset is generated once into `../datasets-shared/` and shared by all the
connector benchmarks that use the `k, name, value, flag` schema.

## License

`pw.io.mysql.write` is a licensed feature — set `PATHWAY_LICENSE_KEY` before
running (the benchmark image forwards it into the container).

## Methodology

* **Dataset.** `k` (BIGINT, `0..rows-1`), `name` (TEXT, `"item_<k>"`), `value`
  (DOUBLE), `flag` (BOOLEAN), in 64 CSV shards. The directory is mounted
  read-only into the Pathway container.
* **Measured run.** Pathway performs a **bounded** read,
  `pw.io.csv.read(mode="static")` over the shard directory, and writes every row
  to MySQL with `pw.io.mysql.write` (default `output_table_type="stream_of_changes"`,
  which appends `time BIGINT`/`diff` metadata columns; every row of a static input
  is an insertion, so every `diff` is `1`). The table is recreated each run with
  `init_mode="replace"`. The reported number is the wall-clock of `pw.run()`: read
  + CSV parse + write of the whole dataset, end-to-end.
* **Worker count = `PATHWAY_THREADS`.** The CSV reader is sharded across workers
  (one reader per worker, capped); the rows are written to MySQL with one
  connection per worker (stream-of-changes output is per-worker).
* **Repetition + median.** Each worker count is run `--reps` times (default 3);
  the **median** end-to-end time is reported, with the individual run times shown
  alongside.
* **Speed *and* correctness.** After each run — **outside the timed window**, over
  the MySQL wire protocol — the benchmark verifies the exact row count and data
  integrity: the `k` range and sum (catching missing/duplicate/garbled keys), the
  derived `name` column, the absence of nulls, and that every appended row is an
  insertion (`sum(diff)` equals the row count). A run only counts as `ok=True` if
  every check passes.

## Machine specs

Single-socket **AMD Ryzen 9 5900X** (Zen 3, 12 cores / 24 threads, **one NUMA
node**), 125 GiB RAM, NVMe SSD. The 12 cores are split across **two core-complex
dies (CCDs) of 6 cores each, each with its own 32 MiB L3**. MySQL is pinned to
CCD 0 (`0-5,12-17`) and the Pathway engine to CCD 1 (`6-11,18-23`), so each
service gets a private L3 and never shares a physical core with the other —
identical placement to the QuestDB/PostgreSQL benchmarks. MySQL is the `mysql:8.0`
Docker image configured for write throughput — relaxed durability
(`innodb_flush_log_at_trx_commit=2`, `sync_binlog=0`, `innodb_doublewrite=0`) plus a
4 GiB buffer pool and 4 GiB redo log — so the write is not gated by a per-commit
`fsync`. See *Server durability and worker scaling* for the stock-vs-configured
comparison.

## Write path and scaling

The MySQL output connector bulk-writes each batch. At start-up it probes the server
and selects a write path: if the server allows `LOAD DATA LOCAL INFILE`
(`local_infile=ON`) it streams each batch through that; otherwise (the image
default, `local_infile=OFF`) it uses chunked multi-row `INSERT`, which for this row
shape is the faster of the two. Each Pathway worker drives its own connection
(stream-of-changes output is per-worker), so on a server that can absorb concurrent
commits the write scales with workers: ~190 000 rows/s at one worker up to ~279 000
at eight (1.45×; see *Results*).

The scaling is **sub-linear**: one bulk writer already achieves a large share of
the throughput, and all workers write into a **single** InnoDB table, so they
contend on that table's redo buffer and clustered-index hot spot. Partitioning the
target table (or writing to several tables) would let concurrent writers scale
further.

## Results

End-to-end wall-clock time to read the 5 M-row, 64-shard CSV dataset (**≈ 0.23
GB**, ≈ 45 bytes/row) and land every row in MySQL, swept over 1/2/4/8 Pathway
workers (median of 3 runs, throughput-configured `mysql:8.0`, on an otherwise idle
host). "Source bytes/s" is the input CSV byte rate (rows/s × ≈ 45 B/row).

> **These headline numbers are measured with relaxed durability** — no per-commit
> `fsync`, a benchmark-only server configuration. On the stock `mysql:8.0`
> durability settings the same pipeline lands ≈ 52 800 rows/s at one worker and
> does not scale with workers; see *Server durability and worker scaling* for the
> side-by-side comparison.

| Pathway workers | End-to-end time | Throughput | Source bytes/s | Speedup |
|---:|---:|---:|---:|---:|
| 1 | 26.0 s | ≈ 192 300 rows/s | ≈ 8.7 MB/s | 1.00× |
| 2 | 21.9 s | ≈ 228 700 rows/s | ≈ 10.3 MB/s | 1.19× |
| 4 | 20.5 s | ≈ 244 400 rows/s | ≈ 11.0 MB/s | 1.27× |
| 8 | 17.9 s | ≈ 278 900 rows/s | ≈ 12.5 MB/s | 1.45× |

Every run passed the integrity checks (`ok=True`). Throughput scales across the
whole sweep to **~279 000 rows/s at 8 workers** (1.45×). The scaling is sub-linear
because all workers funnel into one InnoDB table and contend on its redo buffer and
clustered-index hot spot. Single-worker throughput (~192 000 rows/s) is within
range of the binary-`COPY`/native-bulk sinks in this suite (PostgreSQL, ClickHouse,
QuestDB). On the stock server durability configuration the write does not scale;
see the next section.

## Server durability and worker scaling

On the stock `mysql:8.0` durability configuration the write does not scale — it
peaks at 2 workers and returns to the single-worker rate:

| workers | stock `mysql:8.0` (default durability) | configured (relaxed durability) |
|---:|---:|---:|
| 1 | ≈ 52 800 rows/s | ≈ 192 300 rows/s |
| 2 | ≈ 65 000 rows/s (peak) | ≈ 228 700 rows/s |
| 4 | ≈ 53 000 rows/s | ≈ 244 400 rows/s |
| 8 | ≈ 49 000 rows/s (0.93×) | ≈ 278 900 rows/s (1.45×) |

The default `innodb_flush_log_at_trx_commit=1` performs an `fsync` of the redo log
on every transaction commit, and `sync_binlog=1` does the same for the binary log.
The connector commits each batch, so throughput is bounded by how many durable
commits the disk can `fsync` per second — a server-wide ceiling that a single bulk
writer already reaches. Additional Pathway workers add more concurrent commits
contending on the one redo log; the total does not grow, and at 8 workers regresses
slightly under the extra contention. The bottleneck in this configuration is
MySQL's durable-commit rate, not the connector or the read.

The benchmark therefore starts the server with durability relaxed (in
`docker-compose.yml`):

```
--innodb-flush-log-at-trx-commit=2   # flush+fsync redo once per second, not per commit
--sync-binlog=0                      # let the OS flush the binlog, no per-commit fsync
--innodb-doublewrite=0               # skip the doublewrite buffer
--innodb-buffer-pool-size=4G         # keep the working set in memory
--innodb-redo-log-capacity=4G        # avoid redo-log throttling under sustained writes
```

Removing the per-commit `fsync` raises the single-worker ceiling ~3.6×
(52.8k → 192.3k) and lets concurrent writers add throughput rather than contend, so
the write scales to 8 workers (1.45×, ~279k rows/s). These settings trade
crash-safety for throughput and are appropriate for a benchmark rather than a
production configuration; a production system requiring both durability and higher
throughput would partition the target table or provision faster storage rather than
disable `fsync`.

## Reproducing

From this directory:

```bash
python run_mysql_bulk_write.py                          # 5M rows, workers 1 2 4 8
python run_mysql_bulk_write.py --workers 1 --reps 1     # quick single check
python run_mysql_bulk_write.py --rows 200000 --workers 1 --reps 1   # calibration probe
```
