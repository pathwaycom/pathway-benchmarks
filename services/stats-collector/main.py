import argparse
import subprocess
import time


def calculate_stats(collector_args):
    start_at = time.time()

    args = "cargo run --bin {}".format(collector_args).split()
    print("Command to be executed: ", args)

    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()

    finish_at = time.time()
    print("Time spent on stats:", finish_at - start_at)


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
    parser.add_argument("--stats_short", type=int, default=1)
    parser.add_argument("--stats_timeline", type=int, default=1)
    parser.add_argument("--stats_pathway_ptime_aggregated", type=int, default=1)
    args = parser.parse_args()

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

    cargo_run_command = "{} {} --stats_short {} --stats_timeline {} --stats_pathway_ptime_aggregated {}".format(
        args.type + "_stats_collector",
        instance_name,
        args.stats_short,
        args.stats_timeline,
        args.stats_pathway_ptime_aggregated,
    )

    print("Instance name:", instance_name)
    calculate_stats(cargo_run_command)
