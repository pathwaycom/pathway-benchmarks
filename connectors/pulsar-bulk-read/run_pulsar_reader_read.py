"""Run the Pulsar bulk-read benchmark in the partition-reader mode.

Same two containers and the same dataset as ``run_pulsar_bulk_read.py``, but
the benchmark topic is created as a **partitioned** topic (8 partitions by
default, so it divides evenly across every measured worker count) and the
measured runs read it with ``subscription_type="reader"`` — the Kafka-like
mechanism where every partition is consumed as an independent log and the
read positions live on the Pathway side. The sweep is run twice: without and
with persistence (the reader mode is the only one compatible with it).

The reader mode leaves no broker-side subscription whose backlog could be
polled, so completion is detected by an in-graph row counter built into
``main_reader.py``: the pipeline prints ``T0`` right before ``pw.run()`` and
``T1=<unix seconds> CNT=<rows>`` whenever the counter reaches the expected
row count. The elapsed time is ``T1 - T0``; the run is correct iff the final
``CNT`` equals the row count exactly (the run script waits a few extra
seconds after the first ``T1`` so that any trailing duplicates would surface
as a larger final counter).

Usage:
    python run_pulsar_reader_read.py                       # workers 1 2 4 8
    python run_pulsar_reader_read.py --workers 8 --reps 1  # quick check
    python run_pulsar_reader_read.py --rows 200000 --workers 1 --reps 1  # calibration probe
"""

import argparse
import json
import os
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
TOPIC = "bench_in_p8"
HOLDER_SUBSCRIPTION = "retention-holder"
COMPLETION_TIMEOUT = 1800.0


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


def admin_retry(method: str, path: str, body: str | None = None):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        try:
            return admin_req(method, path, body)
        except urllib.error.HTTPError as e:
            if e.code == 409:  # already exists
                return None
            time.sleep(1)
        except Exception:
            time.sleep(1)
    raise SystemExit(f"admin call failed: {method} {path}")


def create_partitioned_topic(partitions: int) -> None:
    admin_retry(
        "PUT", f"/persistent/public/default/{TOPIC}/partitions", str(partitions)
    )


def create_holder_subscription() -> None:
    # The reader mode leaves no broker-side subscriptions, so a subscription
    # that never acknowledges anything must pin the prefilled backlog — same
    # role as in the shared-subscription benchmark.
    admin_retry(
        "PUT",
        f"/persistent/public/default/{TOPIC}/subscription/{HOLDER_SUBSCRIPTION}",
    )


def topic_message_count() -> int:
    try:
        stats = admin_req(
            "GET", f"/persistent/public/default/{TOPIC}/partitioned-stats"
        )
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


def prefill(rows: int, fill_workers: int, partitions: int) -> None:
    create_partitioned_topic(partitions)
    if topic_message_count() >= rows:
        print("topic already prefilled")
        return
    create_holder_subscription()
    env = dict(os.environ)
    env["DATASET_SIZE"] = str(rows)
    env["PATHWAY_THREADS"] = str(fill_workers)
    env["PULSAR_TOPIC"] = TOPIC
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


def container_logs(container: str) -> str:
    logs = subprocess.run(["docker", "logs", container], capture_output=True, text=True)
    return logs.stdout + logs.stderr


def run_measured(rows: int, workers: int, persistence: bool) -> tuple[float, bool]:
    env = dict(os.environ)
    env["DATASET_SIZE"] = str(rows)
    env["PATHWAY_THREADS"] = str(workers)
    env["PULSAR_TOPIC"] = TOPIC
    env["PERSISTENCE"] = "1" if persistence else "0"
    env["BENCH_ENTRYPOINT"] = "main_reader.py"
    container = f"{PROJECT}-reader-{uuid4().hex[:8]}"
    sh(
        COMPOSE + ["run", "-d", "--rm", "--name", container, "pathway"],
        env=env,
        check=True,
    )
    try:
        t0 = t1 = None
        cnt = -1
        deadline = time.monotonic() + COMPLETION_TIMEOUT
        while time.monotonic() < deadline:
            out = container_logs(container)
            if t0 is None:
                for line in out.splitlines():
                    if line.startswith("T0="):
                        t0 = float(line.split("=", 1)[1])
                        break
            t1_lines = [ln for ln in out.splitlines() if ln.startswith("T1=")]
            if t1_lines:
                t1 = float(t1_lines[0].split()[0].split("=", 1)[1])
                # Give trailing duplicates (if any) a chance to surface, then
                # take the last reported counter value.
                time.sleep(5)
                t1_lines = [
                    ln
                    for ln in container_logs(container).splitlines()
                    if ln.startswith("T1=")
                ]
                cnt = int(t1_lines[-1].split("CNT=", 1)[1])
                break
            time.sleep(0.3)
        if t0 is None or t1 is None:
            print(container_logs(container)[-3000:])
            raise SystemExit("the run did not complete in time")
        ok = cnt == rows
        if not ok:
            print(f"  CORRECTNESS CHECK FAILED: CNT={cnt} != {rows}")
        return t1 - t0, ok
    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=20_000_000)
    p.add_argument("--shards", type=int, default=64)
    p.add_argument("--workers", type=int, nargs="+", default=[1, 2, 4, 8])
    p.add_argument("--fill-workers", type=int, default=8)
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--partitions", type=int, default=8)
    args = p.parse_args()

    gen_dataset(args.rows, args.shards)
    sh(COMPOSE + ["build", "pathway"])
    sh(COMPOSE + ["up", "-d", "--wait", "pulsar"])

    results = []
    try:
        prefill(args.rows, args.fill_workers, args.partitions)
        for persistence in (False, True):
            for w in args.workers:
                runs = [
                    run_measured(args.rows, w, persistence) for _ in range(args.reps)
                ]
                times = [t for t, _ in runs]
                results.append(
                    {
                        "persistence": persistence,
                        "workers": w,
                        "median": statistics.median(times),
                        "rows_per_second": args.rows / statistics.median(times),
                        "ok": all(ok for _, ok in runs),
                        "runs": times,
                    }
                )
    finally:
        sh(COMPOSE + ["down", "-v"])

    print(
        f"\n============ READER-MODE RESULTS  ({args.rows:,} rows, "
        f"{args.partitions} partitions, median of {args.reps}) ============"
    )
    print(
        f"{'pers':>6}{'workers':>8}{'median_s':>11}{'rows/s':>14}"
        f"{'speedup':>9}{'ok':>5}   runs(s)"
    )
    for persistence in (False, True):
        group = [r for r in results if r["persistence"] == persistence]
        if not group:
            continue
        base = group[0]["rows_per_second"]
        for r in group:
            runs_str = ", ".join(f"{t:.1f}" for t in r["runs"])
            print(
                f"{'yes' if persistence else 'no':>6}"
                f"{r['workers']:>8}{r['median']:>11.2f}"
                f"{r['rows_per_second']:>14,.0f}"
                f"{r['rows_per_second'] / base:>8.2f}x{str(r['ok']):>5}   {runs_str}"
            )


if __name__ == "__main__":
    main()
