# QuestDB Bulk-Write Benchmark

Measures how fast the Pathway Live Data Framework writes a dataset into QuestDB
with `pw.io.questdb.write`, end-to-end, and how it scales with the number of
Pathway workers. Rows are read from a directory of **CSV shards** and written to
QuestDB over the InfluxDB Line Protocol (ILP).

This benchmark uses the **parallelized filesystem reader**: each input shard is
owned by exactly one worker (chosen by a stable hash of its path), so the read
parallelizes across workers, and the QuestDB ILP connector is multi-threaded, so
each worker also drives its own ILP write stream. The worker sweep therefore
scales **both** the read and the write (see "Parallelized input" below).

Two containers wired by `docker-compose`: **QuestDB** and **Pathway**.

> **This is not a QuestDB benchmark.** It measures the *full cycle* — the Pathway
> engine reading the input source, doing very basic per-row processing, and
> writing to QuestDB over ILP — so every number reflects **Pathway + the input
> source + QuestDB together**, out of the box. It must not be read as QuestDB's
> standalone ingestion ceiling, which is considerably higher with a tuned worker
> pool (see "Machine specs" below).
>
> **Scope.** This is not meant to be comprehensive benchmarking. The goal was
> simply to confirm that Pathway can keep up with **millions of rows per second**
> — a canonical QuestDB workload — and the runs below verify exactly that.

## Layout

```
questdb-bulk-write/
├── datasets/questdb-bulk-gen.py           # sharded dataset generator (k, name, value, flag)
├── docker-compose/
│   ├── docker-compose.yml                 # questdb + pathway, two containers
│   └── variables.env                      # dataset size, core pinning, port
├── services/pathway-all/
│   ├── Dockerfile                         # installs the latest Pathway nightly + main.py
│   └── main.py                            # read CSV shards -> questdb.write, time pw.run()
└── run_questdb_bulk_write.py              # generate, run per worker count, report
```

## License

The QuestDB output connector is a licensed Pathway feature. Set
`PATHWAY_LICENSE_KEY` in your environment before running; the run script passes
it through to the Pathway container. Get a key at
<https://pathway.com/get-license/>.

## Parallelized input

This benchmark uses the **parallelized filesystem reader**: each input shard is
owned by exactly one worker, chosen by a stable hash of its path (deterministic
across workers, no coordination), so the read parallelizes across workers up to
one reader per worker. Combined with the multi-threaded ILP writer, the worker
sweep scales **both** the read and the write.

This image installs the latest **Pathway nightly** via `pip install --pre`.

## Methodology

What is measured, and how:

* **Dataset.** The generator writes the rows — `k` (BIGINT, `0..rows-1`), `name`
  (TEXT, `"item_<k>"`), `value` (DOUBLE), `flag` (BOOLEAN) — into `--shards` CSV
  files (64 by default) under `datasets/input_<rows>/`. The directory is mounted
  read-only into the Pathway container. At the default 20 M rows this is
  **≈ 0.93 GB** of CSV (≈ 47 bytes/row) — worth keeping in mind alongside the row
  count, since throughput in bytes/s is often the more comparable figure.
* **Measured run.** Pathway performs a **bounded** read,
  `pw.io.csv.read(mode="static")` over the shard directory — it reads every shard
  to the end and then `pw.run()` terminates — and writes every row to QuestDB
  with `pw.io.questdb.write`. The reported number is the wall-clock of
  `pw.run()`: read + CSV parse + ILP write of the whole dataset, end-to-end.
* **The measured time is not "pure".** It is the whole pipeline end-to-end, which
  includes one-time startup costs before any row is written: constructing the
  Pathway dataflow graph (this part runs in Python), spinning up the engine
  (lightweight, but not free), and connector pre-flight — e.g. the QuestDB writer
  first checks that the endpoint/table is reachable before it starts streaming.
  These fixed costs are small but non-zero, and on a ~13–22 s run they are not
  negligible. If you care about the exact throughput boundary, run a **larger
  dataset**: the fixed startup amortizes away and the steady-state rate dominates.
* **Worker count = `PATHWAY_THREADS`.** The CSV reader is sharded across workers
  (one reader per worker, capped) and the rows are written to QuestDB in parallel
  (the ILP connector is multi-threaded), so the sweep scales the **whole**
  pipeline — both the read and the write.
* **Repetition + median.** Each worker count is run `--reps` times (default 3);
  the **median** end-to-end time is reported, with the individual run times shown
  alongside.
* **Speed *and* correctness.** We measure throughput, but we also check that the
  data actually landed intact. After each run — **outside the timed window**,
  over the QuestDB HTTP endpoint — the benchmark verifies the exact row count and
  the data integrity: the `k` range and sum (catching any missing, duplicate or
  garbled keys), the derived `name` column, and the absence of nulls. A run only
  counts as `ok=True` if every check passes. The verification runs after
  `pw.run()` has returned, so it is never part of the measured time; the QuestDB
  table is dropped before each run.

## Machine specs

Results below were obtained on a single-socket **AMD Ryzen 9 5900X** (Zen 3, 12
cores / 24 threads, **one NUMA node**), 125 GiB of RAM, with an **NVMe SSD**
backing the QuestDB data directory. The CPU governor was set to `performance`.

QuestDB is the stock **`questdb/questdb:latest`** Docker image (here **9.4.2**)
at its **default configuration** — the only setting changed is ILP partitioning
by day. In particular we did **not** raise QuestDB's worker-thread count. QuestDB
ingestion scales strongly with its worker pool — QuestDB's own
[InfluxDB-vs-QuestDB comparison](https://questdb.com/blog/influxdb-vs-questdb-comparison/)
reports far higher rates with 32 workers — so a tuned QuestDB would land these
rows faster. The numbers here are deliberately "out of the box", which is the
point: this measures the full Pathway→QuestDB cycle as a user would get it
without database tuning, not QuestDB at its peak.

The 5900X is a single NUMA node, but it has a topology that matters here: its 12
cores are split across **two core-complex dies (CCDs) of 6 cores each, and each
CCD has its own 32 MiB L3 cache** (64 MiB total, in two instances). Cores within
a CCD share their L3; cores on different CCDs do not, and traffic between them
crosses the Infinity Fabric. Per-core caches are 32 KiB L1d, 32 KiB L1i and
512 KiB L2. So the locality unit that keeps a client–server handoff fast is the
shared-L3 CCD, just as a NUMA node is on a multi-socket box.

The two containers are pinned to **one CCD each**: QuestDB owns CCD 0 / L3 #0
(cores `0-5` plus their SMT siblings `12-17`) and the Pathway engine owns CCD 1 /
L3 #1 (cores `6-11` plus `18-23`). Each service therefore gets a private 32 MiB
L3 and never shares a physical core with the other; the largest worker count (8)
fits on CCD 1 (it uses SMT threads beyond 6 workers). Everything stays on the
single NUMA node, so all memory is local; placement follows Linux's first-touch
policy. Adjust `QUESTDB_CPUSET` / `PATHWAY_CPUSET` in
`docker-compose/variables.env` to match your topology — read it from `lscpu` and
the per-core L3 `shared_cpu_list` under
`/sys/devices/system/cpu/*/cache/index3/`.

## Results

End-to-end wall-clock time to read the 20 M-row, 64-shard CSV dataset (**≈ 0.93
GB**) and land every row in QuestDB, swept over 1/2/4/8 Pathway workers (median of
3 runs):

| Pathway workers | End-to-end time | Throughput | Speedup |
|---:|---:|---:|---:|
| 1 | 22.5 s | ≈ 890 000 rows/s | 1.00× |
| 2 | 12.5 s | ≈ 1 600 000 rows/s | 1.80× |
| 4 | 10.1 s | ≈ 1 986 000 rows/s | 2.23× |
| 8 | 9.5 s | ≈ 2 116 000 rows/s | 2.38× |

Every run passed the integrity checks (`ok=True`) — the rows are not just fast,
they are correct. With the read fully parallelized and each worker driving its
own ILP stream, throughput **scales cleanly with the worker count** — 1.80× at 2
workers, 2.23× at 4, and **2.38× at 8 for a peak of ~2.1 M rows/s** — and the
runs are remarkably stable (the 2-worker runs landed at 12.5 s three times in a
row).

These numbers were taken on an otherwise idle machine. QuestDB ingestion also
scales strongly with *its own* worker pool (see "Machine specs"), so a tuned
QuestDB would push the ceiling higher still — these are deliberately the
out-of-the-box rates.

## Reproducing

From this directory:

```bash
export PATHWAY_LICENSE_KEY=...                         # required for the connector
python run_questdb_bulk_write.py                      # 20M rows, workers 1 2 4 8
python run_questdb_bulk_write.py --workers 4 --reps 1 # quick single check
```

The script generates the 64-shard dataset (or reuses an existing one), builds the
Pathway image, starts QuestDB, then for each worker count runs `--reps` passes,
verifies row count and data integrity over the QuestDB HTTP endpoint (outside the
timed window), and prints the median table.
