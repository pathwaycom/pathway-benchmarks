"""Run the Pulsar bulk-read benchmark across Pathway worker counts.

Two containers (Pulsar standalone + Pathway). The benchmark topic is prefilled
once (``fill.py`` publishes every row of the generated CSV dataset as one JSON
message), guarded by a retention-holder subscription so the backlog survives
between runs. Each measured run then streams the topic through
``pw.io.pulsar.read`` with a fresh shared subscription into a null sink; all
the Pathway workers attach to the same subscription, so the read parallelizes
across them.

A streaming read never finishes on its own, so the run script watches the
subscription backlog over the admin API: the elapsed time is the interval from
the ``T0`` printed by the pipeline (right before ``pw.run()``) to the moment
the backlog reaches zero, and the container is stopped afterwards. For each
worker count the run is repeated ``--reps`` times and the median is reported.

Usage:
    python run_pulsar_bulk_read.py                       # workers 1 2 4 8
    python run_pulsar_bulk_read.py --workers 8 --reps 1  # quick check
    python run_pulsar_bulk_read.py --rows 200000 --workers 1 --reps 1  # calibration probe
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
from uuid import uuid4

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

SHARED_DATASETS = os.path.join(ROOT, "..", "datasets-shared")
GEN = os.path.join(SHARED_DATASETS, "bulk-gen.py")

PROJECT = (os.environ.get("USER", "pulsarread") + "_pulsarread").replace(".", "_")
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
TOPIC = "bench_in"
HOLDER_SUBSCRIPTION = "retention-holder"
COMPLETION_TIMEOUT = 1800.0


def sh(cmd, **kw):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    return subprocess.run(cmd, **kw)


def admin_port() -> str:
    return os.environ.get("PULSAR_ADMIN_PORT", "18080")


def admin_req(method: str, path: str):
    url = f"http://127.0.0.1:{admin_port()}/admin/v2{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else None


def create_holder_subscription() -> None:
    # A subscription that never acknowledges anything: it pins the prefilled
    # backlog, so the broker doesn't delete the messages once the measured
    # subscriptions consume them.
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            admin_req(
                "PUT",
                f"/persistent/public/default/{TOPIC}/subscription/{HOLDER_SUBSCRIPTION}",
            )
            return
        except urllib.error.HTTPError as e:
            if e.code == 409:  # already exists
                return
            time.sleep(1)
        except Exception:
            time.sleep(1)
    raise SystemExit("could not create the retention-holder subscription")


def subscription_backlog(subscription: str) -> int:
    try:
        stats = admin_req("GET", f"/persistent/public/default/{TOPIC}/stats")
        sub = stats.get("subscriptions", {}).get(subscription)
        if sub is None:
            return -1
        return int(sub.get("msgBacklog", -1))
    except Exception:
        return -1


def topic_message_count() -> int:
    try:
        stats = admin_req("GET", f"/persistent/public/default/{TOPIC}/stats")
        return int(stats.get("msgInCounter", -1))
    except Exception:
        return -1


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


def prefill(rows: int, fill_workers: int) -> None:
    if topic_message_count() >= rows:
        print("topic already prefilled")
        return
    create_holder_subscription()
    env = dict(os.environ)
    env["DATASET_SIZE"] = str(rows)
    env["PATHWAY_THREADS"] = str(fill_workers)
    env["BENCH_ENTRYPOINT"] = "fill.py"
    res = subprocess.run(
        COMPOSE + ["run", "--rm", "pathway"], env=env, capture_output=True, text=True
    )
    if "FILL_DONE" not in res.stdout + res.stderr:
        print(res.stdout + res.stderr)
        raise SystemExit("prefill did not finish")
    count = topic_message_count()
    if count != rows:
        raise SystemExit(f"prefill count mismatch: {count} != {rows}")


def run_measured(rows: int, workers: int) -> tuple[float, bool]:
    subscription = f"bench-{uuid4().hex[:8]}"
    env = dict(os.environ)
    env["DATASET_SIZE"] = str(rows)
    env["PATHWAY_THREADS"] = str(workers)
    env["PULSAR_SUBSCRIPTION"] = subscription
    container = f"{PROJECT}-reader-{subscription}"
    sh(
        COMPOSE + ["run", "-d", "--rm", "--name", container, "pathway"],
        env=env,
        check=True,
    )
    try:
        # Wait for the pipeline to report T0 (printed right before pw.run()).
        t0 = None
        deadline = time.monotonic() + 300
        while t0 is None and time.monotonic() < deadline:
            logs = subprocess.run(
                ["docker", "logs", container], capture_output=True, text=True
            )
            match = re.search(r"T0=([0-9.]+)", logs.stdout + logs.stderr)
            if match:
                t0 = float(match.group(1))
            else:
                time.sleep(0.2)
        if t0 is None:
            raise SystemExit("pipeline did not report T0")

        deadline = time.monotonic() + COMPLETION_TIMEOUT
        while time.monotonic() < deadline:
            backlog = subscription_backlog(subscription)
            if backlog == 0:
                end = time.time()
                return end - t0, True
            time.sleep(0.5)
        raise SystemExit("the subscription backlog did not drain in time")
    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True)
        # Drop the measured subscription so it doesn't pin the backlog.
        try:
            admin_req(
                "DELETE",
                f"/persistent/public/default/{TOPIC}/subscription/{subscription}?force=true",
            )
        except Exception:
            pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=20_000_000)
    p.add_argument("--shards", type=int, default=64)
    p.add_argument("--workers", type=int, nargs="+", default=[1, 2, 4, 8])
    p.add_argument("--fill-workers", type=int, default=8)
    p.add_argument("--reps", type=int, default=3)
    args = p.parse_args()

    gen_dataset(args.rows, args.shards)
    sh(COMPOSE + ["build", "pathway"])
    sh(COMPOSE + ["up", "-d", "--wait", "pulsar"])

    results = []
    try:
        prefill(args.rows, args.fill_workers)
        for w in args.workers:
            runs = [run_measured(args.rows, w) for _ in range(args.reps)]
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
    print(
        f"\n==================== RESULTS  ({args.rows:,} rows, "
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
