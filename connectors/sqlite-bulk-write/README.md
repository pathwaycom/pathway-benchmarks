# SQLite Bulk-Write Benchmark

Measures how fast the Pathway Live Data Framework writes a dataset into a
**SQLite** database file with `pw.io.sqlite.write`, end-to-end, and how it
behaves as the number of Pathway workers grows. Rows are read from a directory of
**CSV shards** and written to a single SQLite file.

This is the QuestDB/PostgreSQL bulk-write benchmark with the database swapped for
SQLite: the **same dataset schema**, the **same end-to-end timing**, and the
**same out-of-band correctness verification**. SQLite is an **embedded,
single-writer** database (one file guarded by a database-level write lock, no
server process), so the write does not scale across workers: concurrent workers
serialize on the one file. The worker sweep therefore characterizes single-writer
behavior rather than write parallelism.

One container wired by `docker-compose`: **Pathway** only (SQLite is embedded; the
output file lives on a bind-mounted `./out` directory so it can be verified
out-of-band).

> **This is not a SQLite benchmark.** It measures the *full cycle* — Pathway
> reading the input source, light per-row processing, and writing to a SQLite
> file — so every number reflects **Pathway + the input source + SQLite
> together**, out of the box.

## Dataset size

At a single writer a calibration probe (0.2 M rows, 1 worker) measured
**≈ 230 000 rows/s**, so a 20 M-row single-worker run is ~1.5 minutes. This
benchmark therefore uses the full **20 000 000 rows** (≈ 0.93 GB of CSV, ≈ 46.7
bytes/row), the same as the fast sinks, so the single-worker number is directly
comparable. The multi-worker points measure the cost of directing several workers
at the one file (see "Results").

## Layout

```
sqlite-bulk-write/
├── docker-compose/
│   ├── docker-compose.yml                 # pathway only (SQLite is embedded)
│   └── variables.env                      # dataset size, batch, core pinning
├── services/pathway-all/
│   ├── Dockerfile                         # installs the latest Pathway nightly + main.py
│   └── main.py                            # read CSV shards -> sqlite.write, time pw.run()
└── run_sqlite_bulk_write.py               # generate, run per worker count, report
```

The dataset is generated once into `../datasets-shared/` and shared by all the
connector benchmarks that use the `k, name, value, flag` schema.

## License

`pw.io.sqlite.write` is **not** a licensed feature — no `PATHWAY_LICENSE_KEY` is
required.

## Methodology

* **Dataset.** `k`, `name` (`"item_<k>"`), `value`, `flag`, in 64 CSV shards,
  mounted read-only.
* **Measured run.** `pw.io.csv.read(mode="static")`, then `pw.io.sqlite.write`
  (default `output_table_type="stream_of_changes"`, which adds `time`/`diff`
  columns; every row of a static input is an insertion). The output file is
  removed before each run (`init_mode="replace"` also recreates the table). The
  reported number is the wall-clock of `pw.run()`, end-to-end.
* **Worker count = `PATHWAY_THREADS`.** The CSV read is sharded across workers,
  but the SQLite write goes to one file under a single write lock.
* **Repetition + median.** Each worker count is run `--reps` times (default 3);
  the **median** is reported.
* **Speed *and* correctness.** After each run — **outside the timed window**, by
  reading the SQLite file directly — the benchmark verifies the exact row count,
  the `k` range and sum, the derived `name` column, the absence of nulls, and that
  every row is an insertion (`sum(diff) == count`).

## Machine specs

Single-socket **AMD Ryzen 9 5900X** (Zen 3, 12 cores / 24 threads, **one NUMA
node**), 125 GiB RAM, NVMe SSD. SQLite is embedded (no server), so only the
Pathway engine is pinned — to CCD 1 (`6-11,18-23`), the same CCD the engine uses
in the other benchmarks, so single-worker numbers are comparable.

## Results

End-to-end wall-clock time to read the 20 M-row, 64-shard CSV dataset (**≈ 0.93
GB**, ≈ 46.7 bytes/row) and land every row in a SQLite file, swept over 1/2/4/8
Pathway workers (median of 3 runs, on an otherwise idle host). "Source bytes/s"
is the input CSV byte rate.

| Pathway workers | End-to-end time | Throughput | Source bytes/s | Speedup | Correct? |
|---:|---:|---:|---:|---:|:--|
| 1 | 65.5 s | ≈ 305 300 rows/s | ≈ 14.3 MB/s | 1.00× | ok |
| 2 | 84.9 s | ≈ 235 500 rows/s | ≈ 11.0 MB/s | 0.77× | ok |
| 4 | 81.7 s | ≈ 244 800 rows/s | ≈ 11.4 MB/s | 0.80× | ok |
| 8 | 83.1 s | ≈ 240 600 rows/s | ≈ 11.2 MB/s | 0.79× | ok |

At one worker SQLite lands ~305 000 rows/s and every integrity check passes. The
reference figure for this sink is the single-worker result.

### Multi-worker does not scale (single-writer database)

Beyond one worker the write does not scale — it settles at ~0.77–0.80× of the
single-worker rate, i.e. slightly slower than one worker. The mechanism is as
follows.

SQLite is an embedded **single-writer** database: only one connection may write to
the file at a time (a database-level lock), so the write itself **cannot** run in
parallel no matter how many workers there are. The engine therefore funnels the
whole output through one writer (the connector reports `single_threaded`). With a
**single** Pathway worker that is the *natural* path — the worker reads its shard
and writes it, with nothing to coordinate. With **N > 1** workers the pipeline now
has to do extra work that a single worker never pays for:

1. **Collect** — output rows produced across all N workers must be gathered to the
   one worker that owns the write.
2. **Synchronize** — those rows are consolidated into a single, consistent,
   deterministic stream before they touch the file.
3. **Write** — that stream lands in SQLite, which is single-threaded regardless.

Adding workers therefore introduces a gather-and-consolidate step on top of a
write path that cannot be parallelized: the read parallelizes, but the write is the
binding constraint and the write is intrinsically serial. That coordination
overhead accounts for the ~0.20–0.23× lost at 2/4/8 workers. One worker is both the
fastest and the simplest configuration; concurrent workers cannot write a single
SQLite file in parallel, which is a property of SQLite rather than of Pathway.

Every run lands the complete dataset (`ok=True` at 1/2/4/8 workers). The connector
serializes writers so that exactly one writes at a time, which guarantees a
complete, deterministic result at any worker count; concurrent writers to one
SQLite file are otherwise unsafe (a second writer fails with `SQLITE_BUSY`). For
this sink, a single worker is the recommended and highest-throughput configuration.

## Reproducing

From this directory:

```bash
python run_sqlite_bulk_write.py                          # workers 1 2 4 8
python run_sqlite_bulk_write.py --workers 1 --reps 1     # quick single check
python run_sqlite_bulk_write.py --rows 200000 --workers 1 --reps 1   # calibration probe
```
