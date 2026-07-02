# MS SQL Server Bulk-Write Benchmark

Measures how fast the Pathway Live Data Framework writes a dataset into **Microsoft
SQL Server** with `pw.io.mssql.write`, end-to-end, and how it scales with the
number of Pathway workers. Rows are read from a directory of **CSV shards** and
written to SQL Server.

This is the QuestDB/PostgreSQL bulk-write benchmark with the database swapped for
SQL Server: the **same dataset schema**, the **same core pinning**, the **same
end-to-end timing**, and the **same out-of-band correctness verification**, so the
databases are directly comparable. Like those benchmarks it uses the
**parallelized filesystem reader**, so the worker sweep scales the read; the write
path is discussed below.

Three services wired by `docker-compose`: **SQL Server**, a one-shot
**`mssql-init`** that creates the target database, and **Pathway**.

> **This is not a SQL Server benchmark.** It measures the *full cycle* — Pathway
> reading the input source, light per-row processing, and writing to SQL Server —
> so every number reflects **Pathway + the input source + SQL Server together**,
> out of the box. It is not SQL Server's standalone ingestion ceiling.

## Dataset size

The SQL Server output connector uses SQL Server's **native bulk-load protocol
(`INSERT BULK`)** (see *Write path and scaling* below). At a single worker it lands
~200 000 rows/s, which places it among the faster sinks in this suite.

This benchmark uses **3 000 000 rows** (≈ 0.14 GB of CSV, ≈ 45 bytes/row); a
single-worker run is ~15 s. Throughput is reported in both **rows/s** and **MB/s**
so it stays comparable to the 20 M-row fast benchmarks on a *rate* basis.

## Layout

```
mssql-bulk-write/
├── docker-compose/
│   ├── docker-compose.yml                 # mssql + mssql-init + pathway
│   └── variables.env                      # dataset size, batch, core pinning, port
├── services/pathway-all/
│   ├── Dockerfile                         # installs the latest Pathway nightly + main.py
│   └── main.py                            # read CSV shards -> mssql.write, time pw.run()
└── run_mssql_bulk_write.py                # generate, run per worker count, report
```

The dataset is generated once into `../datasets-shared/` and shared by all the
connector benchmarks that use the `k, name, value, flag` schema.

## License

`pw.io.mssql.write` is a licensed feature — set `PATHWAY_LICENSE_KEY` before
running (the benchmark image forwards it into the container).

## Methodology

* **Dataset.** `k` (BIGINT, `0..rows-1`), `name` (`"item_<k>"`), `value` (float),
  `flag` (bool), in 64 CSV shards, mounted read-only.
* **Measured run.** `pw.io.csv.read(mode="static")`, then `pw.io.mssql.write`
  (default `output_table_type="stream_of_changes"`, which appends `time`/`diff`
  columns; every row of a static input is an insertion, so every `diff` is `1`).
  The table is recreated each run with `init_mode="replace"`. The reported number
  is the wall-clock of `pw.run()`, end-to-end.
* **Worker count = `PATHWAY_THREADS`.** Sharded read across workers; each worker
  drives its own SQL Server connection (stream-of-changes output is per-worker).
* **Repetition + median.** Each worker count is run `--reps` times (default 3);
  the **median** is reported.
* **Speed *and* correctness.** After each run — **outside the timed window**, over
  the TDS protocol — the benchmark verifies the exact row count, the `k` range and
  sum, the derived `name` column, the absence of nulls, and that every row is an
  insertion (`sum(diff) == count`). A run only counts as `ok=True` if every check
  passes.

## Machine specs

Single-socket **AMD Ryzen 9 5900X** (Zen 3, 12 cores / 24 threads, **one NUMA
node**), 125 GiB RAM, NVMe SSD. Two CCDs of 6 cores each, each with a private
32 MiB L3. SQL Server is pinned to CCD 0 (`0-5,12-17`) and the Pathway engine to
CCD 1 (`6-11,18-23`) — identical placement to the QuestDB/PostgreSQL benchmarks.
SQL Server is the stock **`mcr.microsoft.com/mssql/server:2022-latest`** image
(Developer edition) at its default configuration, the same image the Pathway
integration tests use.

## Write path and scaling

The SQL Server output connector streams each batch to the server through the
**native bulk-load protocol (`INSERT BULK`)**. In stream-of-changes mode it
bulk-loads **straight into the target table** when that is provably safe (the
connector created the table this
run, no column name needs bracket-quoting, no `DateTimeUtc` column); otherwise —
and always in snapshot mode — it bulk-loads each batch into a **temporary staging
table** and applies it with a single set-based `INSERT ... SELECT` / `MERGE` /
`DELETE`. Both produce identical results and need no configuration change.

Unlike the MySQL connector (whose bulk write flattens at 1–2 workers because a
stock server `fsync`s the redo log per commit), SQL Server **scales across the
sweep** — each worker drives its own connection and its own bulk-load stream, and
the server absorbs the concurrent streams (see *Results*). Throughput grows with
`max_batch_size` too, since larger minibatches mean fewer, larger bulk transfers.

## Results

End-to-end wall-clock time to read the 3 M-row, 64-shard CSV dataset (**≈ 0.14
GB**, ≈ 45 bytes/row) and land every row in SQL Server, swept over 1/2/4/8 Pathway
workers (median of 3 runs, on an otherwise idle host). "Source bytes/s" is the
input CSV byte rate (rows/s × ≈ 45 B/row).

| Pathway workers | End-to-end time | Throughput | Source bytes/s | Speedup |
|---:|---:|---:|---:|---:|
| 1 | 15.3 s | ≈ 196 600 rows/s | ≈ 8.8 MB/s | 1.00× |
| 2 | 13.0 s | ≈ 230 200 rows/s | ≈ 10.4 MB/s | 1.17× |
| 4 | 11.3 s | ≈ 264 600 rows/s | ≈ 11.9 MB/s | 1.35× |
| 8 | 10.2 s | ≈ 293 500 rows/s | ≈ 13.2 MB/s | 1.49× |

Every run passed the integrity checks (`ok=True`). With the native bulk-load path,
single-worker throughput is **~196 600 rows/s**, and it climbs across the sweep to
**~293 500 rows/s at 8 workers** (1.49×). The scaling is sub-linear — one bulk
writer already moves a large share of the data, so each added worker contributes
less — but throughput increases at every step. SQL Server sits among the faster
sinks in this suite, within range of the binary-`COPY`/native-bulk sinks
(PostgreSQL, ClickHouse, QuestDB).

## Reproducing

From this directory:

```bash
python run_mssql_bulk_write.py                          # 3M rows, workers 1 2 4 8
python run_mssql_bulk_write.py --workers 1 --reps 1     # quick single check
python run_mssql_bulk_write.py --rows 200000 --workers 1 --reps 1   # calibration probe
```
