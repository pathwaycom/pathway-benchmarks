# ClickHouse Bulk-Write Benchmark

Measures how fast the Pathway Live Data Framework writes a dataset into ClickHouse
with `pw.io.clickhouse.write`, end-to-end, and how it scales with the number of
Pathway workers. Rows are read from a directory of **CSV shards** and written to
ClickHouse over its **native protocol** (port 9000).

This is the QuestDB bulk-write benchmark with QuestDB swapped for ClickHouse: the
**same dataset**, the **same core pinning**, the **same end-to-end timing**, and
the **same out-of-band correctness verification**, so the two databases are
directly comparable. Like the QuestDB benchmark it uses the **parallelized
filesystem reader**, so the worker sweep scales *both* the read and the write (see
"Parallelized input" below).

Two containers wired by `docker-compose`: **ClickHouse** and **Pathway**.

> **This is not a ClickHouse benchmark.** It measures the *full cycle* — the
> Pathway engine reading the input source, doing very basic per-row processing,
> and writing to ClickHouse over the native protocol — so every number reflects
> **Pathway + the input source + ClickHouse together**, out of the box. It must
> not be read as ClickHouse's standalone ingestion ceiling, which is considerably
> higher with batching, async inserts and a tuned server.
>
> **Scope.** This is not meant to be comprehensive benchmarking. The goal was
> simply to confirm that Pathway can keep up with **millions of rows per second**
> — a canonical ClickHouse workload — and the runs below verify exactly that.

## Layout

```
clickhouse-bulk-write/
├── datasets/clickhouse-bulk-gen.py        # sharded dataset generator (k, name, value, flag)
├── docker-compose/
│   ├── docker-compose.yml                 # clickhouse + pathway, two containers
│   └── variables.env                      # dataset size, core pinning, port
├── services/pathway-all/
│   ├── Dockerfile                         # installs the latest Pathway nightly + main.py
│   └── main.py                            # read CSV shards -> clickhouse.write, time pw.run()
└── run_clickhouse_bulk_write.py           # generate, run per worker count, report
```

## License

The ClickHouse output connector is a licensed Pathway feature. Set
`PATHWAY_LICENSE_KEY` in your environment before running; the run script passes
it through to the Pathway container. Get a key at
<https://pathway.com/get-license/>.

## Parallelized input

This benchmark uses the **parallelized filesystem reader**: each input shard is
owned by exactly one worker, chosen by a stable hash of its path (deterministic
across workers, no coordination), so the read parallelizes across workers up to
one reader per worker. Combined with the parallel native-protocol writer (each
worker drives its own insert stream), the worker sweep scales **both** the read
and the write.

This image installs the latest **Pathway nightly** via `pip install --pre`.

## Methodology

What is measured, and how:

* **Dataset.** The generator writes the rows — `k` (Int64, `0..rows-1`), `name`
  (String, `"item_<k>"`), `value` (Float64), `flag` (Bool) — into `--shards` CSV
  files (64 by default) under `datasets/input_<rows>/`. The directory is mounted
  read-only into the Pathway container. At the default 20 M rows this is
  **≈ 0.93 GB** of CSV (≈ 47 bytes/row) — worth keeping in mind alongside the row
  count, since throughput in bytes/s is often the more comparable figure. The
  schema is identical to the QuestDB benchmark.
* **Measured run.** Pathway performs a **bounded** read,
  `pw.io.csv.read(mode="static")` over the shard directory — it reads every shard
  to the end and then `pw.run()` terminates — and writes every row to ClickHouse
  with `pw.io.clickhouse.write` (default `output_table_type="stream_of_changes"`,
  which appends `time`/`diff` metadata columns; every row of a static input is an
  insertion, so every `diff` is `1`). The table is recreated each run with
  `init_mode="replace"`. The reported number is the wall-clock of `pw.run()`:
  read + CSV parse + native-protocol write of the whole dataset, end-to-end.
* **The measured time is not "pure".** It is the whole pipeline end-to-end, which
  includes one-time startup costs before any row is written: constructing the
  Pathway dataflow graph (this part runs in Python), spinning up the engine
  (lightweight, but not free), and connector pre-flight — e.g. the ClickHouse
  writer validates the destination table before it starts streaming. These fixed
  costs are small but non-zero, and on short runs they are not negligible. If you
  care about the exact throughput boundary, run a **larger dataset**: the fixed
  startup amortizes away and the steady-state rate dominates.
* **Worker count = `PATHWAY_THREADS`.** The CSV reader is sharded across workers
  (one reader per worker, capped) and the rows are written to ClickHouse in
  parallel, so the sweep scales the **whole** pipeline.
* **Repetition + median.** Each worker count is run `--reps` times (default 3);
  the **median** end-to-end time is reported, with the individual run times shown
  alongside.
* **Speed *and* correctness.** We measure throughput, but we also check that the
  data actually landed intact. After each run — **outside the timed window**,
  over the ClickHouse HTTP endpoint — the benchmark verifies the exact row count
  and the data integrity: the `k` range and sum (catching any missing, duplicate
  or garbled keys), the derived `name` column, the absence of nulls, and that
  every appended row is an insertion (`sum(diff)` equals the row count). A run
  only counts as `ok=True` if every check passes. The verification runs after
  `pw.run()` has returned, so it is never part of the measured time; the
  ClickHouse table is recreated before each run.

## Machine specs

Results below were obtained on a single-socket **AMD Ryzen 9 5900X** (Zen 3, 12
cores / 24 threads, **one NUMA node**), 125 GiB of RAM, with an **NVMe SSD**
backing the ClickHouse data directory. The CPU governor was set to `performance`.

ClickHouse is the stock **`clickhouse/clickhouse-server:latest`** Docker image at
its **default configuration**. We did not tune its background-merge pool, insert
batching or async-insert settings — the numbers here are deliberately "out of the
box", which is the point: this measures the full Pathway→ClickHouse cycle as a
user would get it without database tuning, not ClickHouse at its peak.

The 5900X is a single NUMA node, but it has a topology that matters here: its 12
cores are split across **two core-complex dies (CCDs) of 6 cores each, and each
CCD has its own 32 MiB L3 cache** (64 MiB total, in two instances). Cores within
a CCD share their L3; cores on different CCDs do not, and traffic between them
crosses the Infinity Fabric. Per-core caches are 32 KiB L1d, 32 KiB L1i and
512 KiB L2. So the locality unit that keeps a client–server handoff fast is the
shared-L3 CCD, just as a NUMA node is on a multi-socket box.

The two containers are pinned to **one CCD each** — identically to the QuestDB
benchmark: ClickHouse owns CCD 0 / L3 #0 (cores `0-5` plus their SMT siblings
`12-17`) and the Pathway engine owns CCD 1 / L3 #1 (cores `6-11` plus `18-23`).
Each service therefore gets a private 32 MiB L3 and never shares a physical core
with the other; the largest worker count (8) fits on CCD 1 (it uses SMT threads
beyond 6 workers). Everything stays on the single NUMA node, so all memory is
local; placement follows Linux's first-touch policy. Adjust `CLICKHOUSE_CPUSET` /
`PATHWAY_CPUSET` in `docker-compose/variables.env` to match your topology — read
it from `lscpu` and the per-core L3 `shared_cpu_list` under
`/sys/devices/system/cpu/*/cache/index3/`.

## Results

End-to-end wall-clock time to read the 20 M-row, 64-shard CSV dataset (**≈ 0.93
GB**) and land every row in ClickHouse, swept over 1/2/4/8 Pathway workers (median
of 3 runs):

| Pathway workers | End-to-end time | Throughput | Speedup |
|---:|---:|---:|---:|
| 1 | 29.2 s | ≈ 685 000 rows/s | 1.00× |
| 2 | 27.4 s | ≈ 731 000 rows/s | 1.07× |
| 4 | 16.6 s | ≈ 1 206 000 rows/s | 1.76× |
| 8 | 12.4 s | ≈ 1 619 000 rows/s | 2.36× |

Every run passed the integrity checks (`ok=True`) — the rows are not just fast,
they are correct. Throughput rises to **~1.6 M rows/s at 8 workers** (2.36×), the
fastest point measured, and the per-count runs are stable across repetitions (the
2-worker runs landed at 27.4 / 27.4 / 27.1 s).

The scaling is **uneven**: the step from 1 to 2 workers barely moves the needle
(1.07×), then 2→4→8 scales strongly (1.76× at 4, 2.36× at 8). The flat 1→2 step is
reproducible rather than noise — at low worker counts the gains from the
parallelized read are offset by the two insert streams pressing on ClickHouse's
default background-merge pool; past two workers the parallel read and the multiple
insert streams pay off together and throughput climbs to its peak at 8, even though
the engine's single 6-core CCD means the 8-worker run spills onto SMT siblings (two
threads sharing a physical core). As with the QuestDB and PostgreSQL benchmarks,
these are deliberately out-of-the-box ClickHouse numbers; a tuned merge/insert
configuration would push the ceiling higher.

## Reproducing

From this directory:

```bash
export PATHWAY_LICENSE_KEY=...                           # required for the connector
python run_clickhouse_bulk_write.py                      # 20M rows, workers 1 2 4 8
python run_clickhouse_bulk_write.py --workers 4 --reps 1 # quick single check
```

The script generates the 64-shard dataset (or reuses an existing one), builds the
Pathway image, starts ClickHouse, then for each worker count runs `--reps` passes,
verifies row count and data integrity over the ClickHouse HTTP endpoint (outside
the timed window), and prints the median table.
