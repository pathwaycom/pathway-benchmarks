# Postgres Bulk-Write Benchmark

Measures how fast the Pathway Live Data Framework writes a dataset into
PostgreSQL with `pw.io.postgres.write`, end-to-end, and how it scales with the
number of Pathway workers. Rows are read from a directory of **CSV shards** and
written to PostgreSQL over the database's native binary **`COPY`** protocol —
`pw.io.postgres.write`'s default (and only) write path.

This is the QuestDB bulk-write benchmark with the database swapped for
PostgreSQL: the **same dataset**, the **same core pinning**, the **same
end-to-end timing**, and the **same out-of-band correctness verification**, so
the two databases are directly comparable. Like the QuestDB benchmark it uses the
**parallelized filesystem reader**, so the worker sweep scales *both* the read
and the write (see "Parallelized input" below).

Two containers wired by `docker-compose`: **PostgreSQL** and **Pathway**.

> **This is not a PostgreSQL benchmark.** It measures the *full cycle* — the
> Pathway engine reading the input source, doing very basic per-row processing,
> and writing to PostgreSQL over binary `COPY` — so every number reflects
> **Pathway + the input source + PostgreSQL together**, out of the box. It must
> not be read as PostgreSQL's standalone ingestion ceiling, which is higher with
> a tuned server (`fsync`, `synchronous_commit`, `wal` settings, unlogged tables,
> more cores).
>
> **Scope.** This is not meant to be comprehensive benchmarking. The goal was
> simply to confirm that Pathway can keep up with **hundreds of thousands to
> millions of rows per second** writing into PostgreSQL, and the runs below
> verify exactly that.

## Layout

```
postgres-bulk-write/
├── datasets/postgres-bulk-gen.py          # sharded dataset generator (k, name, value, flag)
├── docker-compose/
│   ├── docker-compose.yml                 # postgres + pathway, two containers
│   └── variables.env                      # dataset size, batch, core pinning, port
├── services/pathway-all/
│   ├── Dockerfile                         # installs the latest Pathway nightly + main.py
│   └── main.py                            # read CSV shards -> postgres.write, time pw.run()
└── run_postgres_bulk_write.py             # generate, run per worker count, report
```

## License

Unlike the QuestDB output connector, `pw.io.postgres.write` is **not** a licensed
feature — no `PATHWAY_LICENSE_KEY` is required to run this benchmark.

## Parallelized input

This benchmark uses the **parallelized filesystem reader**: each input shard is
owned by exactly one worker, chosen by a stable hash of its path (deterministic
across workers, no coordination), so the read parallelizes across workers up to
one reader per worker. Combined with the parallel binary-`COPY` writer (each
worker drives its own `COPY` stream), the worker sweep scales **both** the read
and the write.

This image installs the latest **Pathway nightly** via `pip install --pre`.

## Methodology

What is measured, and how:

* **Dataset.** The generator writes the rows — `k` (BIGINT, `0..rows-1`), `name`
  (TEXT, `"item_<k>"`), `value` (DOUBLE PRECISION), `flag` (BOOLEAN) — into
  `--shards` CSV files (64 by default) under `datasets/input_<rows>/`. The
  directory is mounted read-only into the Pathway container. At the default 20 M
  rows this is **≈ 0.93 GB** of CSV (≈ 47 bytes/row) — worth keeping in mind
  alongside the row count, since throughput in bytes/s is often the more
  comparable figure. The schema is identical to the QuestDB benchmark.
* **Measured run.** Pathway performs a **bounded** read,
  `pw.io.csv.read(mode="static")` over the shard directory — it reads every shard
  to the end and then `pw.run()` terminates — and writes every row to PostgreSQL
  with `pw.io.postgres.write` (default `output_table_type="stream_of_changes"`,
  which appends `time BIGINT`/`diff SMALLINT` metadata columns; every row of a
  static input is an insertion, so every `diff` is `1`). The table is recreated
  each run with `init_mode="replace"`. The write goes over PostgreSQL's native
  binary `COPY` protocol — `pw.io.postgres.write`'s default path, roughly two
  orders of magnitude faster than the row-by-row INSERT loop it replaced against a
  default, `fsync`-on PostgreSQL. The reported number is the wall-clock of
  `pw.run()`: read + CSV parse + binary-`COPY` write of the whole dataset,
  end-to-end.
* **The measured time is not "pure".** It is the whole pipeline end-to-end, which
  includes one-time startup costs before any row is written: constructing the
  Pathway dataflow graph (this part runs in Python), spinning up the engine
  (lightweight, but not free), and connector pre-flight (table creation /
  validation). These fixed costs are small but non-zero, and on short runs they
  are not negligible. If you care about the exact throughput boundary, run a
  **larger dataset**: the fixed startup amortizes away and the steady-state rate
  dominates.
* **Worker count = `PATHWAY_THREADS`.** The CSV reader is sharded across workers
  (one reader per worker, capped) and the rows are written to PostgreSQL in
  parallel (each worker drives its own `COPY` stream), so the sweep scales the
  **whole** pipeline.
* **Repetition + median.** Each worker count is run `--reps` times (default 3);
  the **median** end-to-end time is reported, with the individual run times shown
  alongside.
* **Speed *and* correctness.** We measure throughput, but we also check that the
  data actually landed intact. After each run — **outside the timed window**,
  over the Postgres wire protocol — the benchmark verifies the exact row count
  and the data integrity: the `k` range and sum (catching any missing, duplicate
  or garbled keys), the derived `name` column, the absence of nulls, and that
  every appended row is an insertion (`sum(diff)` equals the row count). A run
  only counts as `ok=True` if every check passes. The verification runs after
  `pw.run()` has returned, so it is never part of the measured time; the table is
  recreated before each run.

## Machine specs

Results below were obtained on a single-socket **AMD Ryzen 9 5900X** (Zen 3, 12
cores / 24 threads, **one NUMA node**), 125 GiB of RAM, with an **NVMe SSD**
backing the PostgreSQL data directory. The CPU governor was set to `performance`.

PostgreSQL is the stock **`postgres:15`** Docker image at its **default
configuration** (`fsync=on`, `synchronous_commit=on`). We did not tune
`shared_buffers`, `wal` settings, or switch to unlogged tables — the numbers here
are deliberately "out of the box", which is the point: this measures the full
Pathway→PostgreSQL cycle as a user would get it without database tuning, not
PostgreSQL at its peak.

The 5900X is a single NUMA node, but it has a topology that matters here: its 12
cores are split across **two core-complex dies (CCDs) of 6 cores each, and each
CCD has its own 32 MiB L3 cache** (64 MiB total, in two instances). Cores within
a CCD share their L3; cores on different CCDs do not, and traffic between them
crosses the Infinity Fabric. Per-core caches are 32 KiB L1d, 32 KiB L1i and
512 KiB L2. So the locality unit that keeps a client–server handoff fast is the
shared-L3 CCD, just as a NUMA node is on a multi-socket box.

The two containers are pinned to **one CCD each** — identically to the QuestDB
benchmark: PostgreSQL owns CCD 0 / L3 #0 (cores `0-5` plus their
SMT siblings `12-17`) and the Pathway engine owns CCD 1 / L3 #1 (cores `6-11`
plus `18-23`). Each service therefore gets a private 32 MiB L3 and never shares a
physical core with the other; the largest worker count (8) fits on CCD 1 (it uses
SMT threads beyond 6 workers). Everything stays on the single NUMA node, so all
memory is local; placement follows Linux's first-touch policy. Adjust
`POSTGRES_CPUSET` / `PATHWAY_CPUSET` in `docker-compose/variables.env` to match
your topology — read it from `lscpu` and the per-core L3 `shared_cpu_list` under
`/sys/devices/system/cpu/*/cache/index3/`.

## Results

End-to-end wall-clock time to read the 20 M-row, 64-shard CSV dataset (**≈ 0.93
GB**) and land every row in PostgreSQL over binary `COPY`, swept over 1/2/4/8
Pathway workers (median of 3 runs):

| Pathway workers | End-to-end time | Throughput | Speedup |
|---:|---:|---:|---:|
| 1 | 35.7 s | ≈ 561 000 rows/s | 1.00× |
| 2 | 27.9 s | ≈ 717 000 rows/s | 1.28× |
| 4 | 17.9 s | ≈ 1 115 000 rows/s | 1.99× |
| 8 | 14.4 s | ≈ 1 394 000 rows/s | 2.48× |

Every run passed the integrity checks (`ok=True`) — the rows are not just fast,
they are correct. Throughput climbs across the **whole** sweep, from ~561 000
rows/s on a single worker to **~1.39 M rows/s at 8 workers** (2.48×), without
plateauing within the measured range.

Two things are worth calling out. First, because this benchmark uses the
**parallelized filesystem reader**, the worker sweep scales the *whole* pipeline
(read + write), so throughput keeps rising at every step rather than flattening
once the write path alone is saturated. Second, the scaling is **sublinear** —
1.28× at 2 workers, 1.99× at 4, 2.48× at 8 — rather than linear, and that is
expected on this hardware: the engine is pinned to a single 6-core CCD, so the
8-worker run spills onto that CCD's SMT siblings (two threads sharing one physical
core), the eight concurrent `COPY` streams share one `fsync`-on PostgreSQL (a
single WAL), and cross-CCD client–server traffic crosses the Infinity Fabric. Even
so, **8 workers is the fastest point measured**: the extra write parallelism still
pays off past the six physical cores, and the 4→8 gain (1.99× → 2.48×) has not yet
been eaten by SMT and WAL contention.

> These numbers come from `pw.io.postgres.write`'s binary-`COPY` path, which is
> the connector's default and what makes bulk writes fast out of the box. It
> replaced a row-by-row INSERT loop that was roughly **two orders of magnitude**
> slower against a default, `fsync`-on server.

## Reproducing

From this directory:

```bash
python run_postgres_bulk_write.py                       # 20M rows, workers 1 2 4 8
python run_postgres_bulk_write.py --workers 4 --reps 1  # quick single check
```

The script generates the 64-shard dataset (or reuses an existing one), builds the
Pathway image, starts PostgreSQL, then for each worker count runs `--reps` passes,
verifies row count and data integrity over the Postgres wire protocol (outside the
timed window), and prints the median table.
