import argparse
import subprocess
import sys
import time


def calculate_stats(collector_args):
    start_at = time.time()

    args = "target/release/{}".format(collector_args).split()
    print("Command to be executed: ", args, file=sys.stderr)

    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()

    finish_at = time.time()
    print("Time spent on stats:", finish_at - start_at, file=sys.stderr)


def wait_for_engine_finish():
    time.sleep(40.0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pathway benchmarker")
    parser.add_argument("--type", type=str, required=True)
    parser.add_argument("--dataset-path", type=str)
    parser.add_argument("--batch-size", type=int, default=10**9)
    parser.add_argument(
        "--input-type",
        type=str,
        choices=["fs", "kafka"],
        default="fs",
    )
    parser.add_argument("--rate-per-second", type=int, default=10**6)
    parser.add_argument("--autocommit-frequency-ms", type=int)
    parser.add_argument("--engine-type", type=str, required=True)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--cores", type=int, default=1)
    parser.add_argument("--stats-short", type=int, default=1)
    parser.add_argument("--stats-timeline", type=int, default=1)
    parser.add_argument("--stats-pathway-ptime-aggregated", type=int, default=1)
    parser.add_argument("--stats-time-aggregated", type=int, default=1)
    parser.add_argument("--skip-prefix-length", type=int, default=0)
    parser.add_argument("--dict-size", type=int, default=5000)

    args = parser.parse_args()

    print("Stats-collector waiting", file=sys.stderr)
    wait_for_engine_finish()

    if not args.autocommit_frequency_ms:
        benchmark_kind = "aware"
    else:
        benchmark_kind = "unaware"

    instance_name = "{}/{}-{}-{}-{}-{}-{}-{}-{}".format(
        args.engine_type,
        args.type,
        time.time(),
        args.workers,
        args.cores,
        args.autocommit_frequency_ms,
        args.batch_size,
        args.rate_per_second,
        benchmark_kind,
    )

    cargo_run_command_f = (
        "{0} {1} "
        + "--stats-short {2} "
        + "--stats-timeline {3} "
        + "--stats-pathway-ptime-aggregated {4} "
        + "--stats-time-aggregated {5} "
        + "--skip-prefix-length {6} "
        + "--dict-size {7}"
    )

    cargo_run_command = cargo_run_command_f.format(
        args.type + "_stats_collector",
        instance_name,
        args.stats_short,
        args.stats_timeline,
        args.stats_pathway_ptime_aggregated,
        args.stats_time_aggregated,
        args.skip_prefix_length,
        args.dict_size,
    )

    print("Instance name:", instance_name)
    calculate_stats(cargo_run_command)
