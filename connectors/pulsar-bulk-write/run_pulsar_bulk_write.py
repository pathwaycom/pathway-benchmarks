"""Run the Pulsar bulk-write benchmark across Pathway worker counts.

Two containers (Pulsar standalone + Pathway). The dataset is generated as CSV
shards; each measured run reads the shard directory (bounded, ``mode="static"``)
and writes every row to a Pulsar topic with ``pw.io.pulsar.write`` (one JSON
message per row). The sharded input lets the filesystem reader parallelize the
read across workers (each shard is owned by exactly one worker, chosen by a
stable hash of its path), so the worker sweep exercises both the parallel read
and the parallel publish. For each worker count the run is repeated ``--reps``
times and the median is reported.

The target topic is (re)created via the admin HTTP API before each run, and the
committed message count is read back from the same API for correctness.

Usage:
    python run_pulsar_bulk_write.py                       # workers 1 2 4 8
    python run_pulsar_bulk_write.py --workers 8 --reps 1  # quick check
    python run_pulsar_bulk_write.py --rows 200000 --workers 1 --reps 1  # calibration probe
    python run_pulsar_bulk_write.py --partitions 8        # 8-partition target topic
"""

import argparse
import json
import os
import re
import statistics
import subprocess
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

SHARED_DATASETS = os.path.join(ROOT, "..", "datasets-shared")
GEN = os.path.join(SHARED_DATASETS, "bulk-gen.py")

PROJECT = (os.environ.get("USER", "pulsarbulk") + "_pulsarbulk").replace(".", "_")
COMPOSE = [
    "docker",
    "compose",
    "--env-file",
    "docker-compose/variables.env",
    "-f",
    "docker-compose/docker-compose.yml",
    "-p",
    PROJECT,
]
TOPIC = "bench_out"


def sh(cmd, **kw):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    return subprocess.run(cmd, **kw)


def admin_port() -> str:
    return os.environ.get("PULSAR_ADMIN_PORT", "18080")


def admin_req(method: str, path: str, body: str | None = None):
    url = f"http://127.0.0.1:{admin_port()}/admin/v2{path}"
    req = urllib.request.Request(
        url, method=method, data=body.encode() if body is not None else None
    )
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else None


def admin_delete(path: str) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            admin_req("DELETE", path)
            return
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return
            time.sleep(1)
        except Exception:
            time.sleep(1)
    raise SystemExit(f"could not delete the Pulsar topic: {path}")


def recreate_topic(partitions: int) -> None:
    # Remove both forms, so that reruns can switch between a plain and a
    # partitioned topic under the same name.
    admin_delete(f"/persistent/public/default/{TOPIC}/partitions?force=true")
    admin_delete(f"/persistent/public/default/{TOPIC}?force=true")
    if partitions:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            try:
                admin_req(
                    "PUT",
                    f"/persistent/public/default/{TOPIC}/partitions",
                    str(partitions),
                )
                return
            except Exception:
                time.sleep(1)
        raise SystemExit("could not create the partitioned topic")


def topic_message_count(partitions: int) -> int:
    stats_endpoint = "partitioned-stats" if partitions else "stats"
    try:
        stats = admin_req("GET", f"/persistent/public/default/{TOPIC}/{stats_endpoint}")
        return int(stats.get("msgInCounter", -1))
    except Exception:
        return -1


def verify_correctness(rows: int, partitions: int) -> tuple[bool, dict]:
    """Verify, over the admin API, that every row became one Pulsar message.

    The topic is deleted before each run, so its ``msgInCounter`` (aggregated
    over the partitions, if any) equals the number of messages published by
    the run. Each message is one row's JSON document; an exact count over a
    fresh topic catches any missing or duplicated rows.
    """
    count = topic_message_count(partitions)
    return count == rows, {"count": count}


def gen_dataset(rows: int, shards: int) -> None:
    out = os.path.join(SHARED_DATASETS, f"input_{rows}")
    if os.path.isdir(out) and os.listdir(out):
        print(f"dataset present: {out}")
        return
    sh(
        [
            "python3",
            GEN,
            "--rows",
            str(rows),
            "--shards",
            str(shards),
            "--output-dir",
            out,
        ]
    )


def run_measured(rows: int, workers: int, partitions: int) -> tuple[float, bool]:
    recreate_topic(partitions)
    env = dict(os.environ)
    env["DATASET_SIZE"] = str(rows)
    env["PATHWAY_THREADS"] = str(workers)
    res = subprocess.run(
        COMPOSE + ["run", "--rm", "pathway"], env=env, capture_output=True, text=True
    )
    out = res.stdout + res.stderr
    elapsed = re.search(r"ELAPSED_SECONDS=([0-9.]+)", out)
    if not elapsed:
        print(out)
        raise SystemExit("pathway run did not report ELAPSED_SECONDS")
    deadline = time.monotonic() + 120
    while topic_message_count(partitions) < rows and time.monotonic() < deadline:
        time.sleep(0.5)
    ok, checks = verify_correctness(rows, partitions)
    if not ok:
        print(f"  CORRECTNESS CHECK FAILED: {checks}")
    return float(elapsed.group(1)), ok


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=20_000_000)
    p.add_argument("--shards", type=int, default=64)
    p.add_argument("--workers", type=int, nargs="+", default=[1, 2, 4, 8])
    p.add_argument("--reps", type=int, default=3)
    p.add_argument(
        "--partitions",
        type=int,
        default=0,
        help="create the target topic with this many partitions "
        "(0 = non-partitioned, the default)",
    )
    args = p.parse_args()

    gen_dataset(args.rows, args.shards)
    sh(COMPOSE + ["build", "pathway"])
    sh(COMPOSE + ["up", "-d", "--wait", "pulsar"])

    results = []
    try:
        for w in args.workers:
            runs = [
                run_measured(args.rows, w, args.partitions) for _ in range(args.reps)
            ]
            times = [t for t, _ in runs]
            median = statistics.median(times)
            results.append(
                {
                    "workers": w,
                    "median": median,
                    "rows_per_second": args.rows / median,
                    "ok": all(ok for _, ok in runs),
                    "runs": times,
                }
            )
    finally:
        sh(COMPOSE + ["down", "-v"])

    base = results[0]["rows_per_second"]
    topic_kind = (
        f"{args.partitions} partitions" if args.partitions else "non-partitioned"
    )
    print(
        f"\n==================== RESULTS  ({args.rows:,} rows, {topic_kind}, "
        f"median of {args.reps}) ===================="
    )
    print(
        f"{'workers':>8}{'median_s':>11}{'rows/s':>14}{'speedup':>9}{'ok':>5}   runs(s)"
    )
    for r in results:
        runs_str = ", ".join(f"{t:.1f}" for t in r["runs"])
        print(
            f"{r['workers']:>8}{r['median']:>11.2f}{r['rows_per_second']:>14,.0f}"
            f"{r['rows_per_second'] / base:>8.2f}x{str(r['ok']):>5}   {runs_str}"
        )


if __name__ == "__main__":
    main()
