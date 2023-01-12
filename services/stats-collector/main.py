import argparse
import subprocess
import time


def calculate_stats(instance_name):
    start_at = time.time()

    args = "cargo run -- {}".format(instance_name).split()
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()

    finish_at = time.time()
    print("Time spent on stats:", finish_at - start_at)


def wait_for_engine_finish():
    time.sleep(120.0)


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
    args = parser.parse_args()

    wait_for_engine_finish()

    if not args.autocommit_frequency_ms:
        benchmark_kind = "aware"
    else:
        benchmark_kind = "unaware"

    instance_name = "{}/{}-{}-{}-{}".format(
        args.engine_type,
        args.type,
        args.batch_size,
        args.rate_per_second,
        benchmark_kind,
    )
    print("Instance name:", instance_name)
    calculate_stats(instance_name)
