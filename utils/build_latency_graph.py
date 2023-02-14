import argparse
import os
import sys
from typing import Dict


def read_timeline(path, shrink_first_lines, shrink_first_milliseconds, percentiles):
    n_rows_read = 0
    first_timestamp_ms = None
    timestamps = []
    with open(path, "r") as f:
        for row in f:
            tokens = [int(x) for x in row.strip().split(",")]
            if len(tokens) != 2:
                continue

            if first_timestamp_ms is None:
                first_timestamp_ms = tokens[0]
            n_rows_read += 1
            if n_rows_read < shrink_first_lines:
                continue
            if tokens[0] - first_timestamp_ms < shrink_first_milliseconds:
                continue
            timestamps.append(int(tokens[1]))

    print(
        "Path: {}, timestamps remained after filtering: {}".format(
            path, len(timestamps)
        )
    )

    timestamps.sort()
    timestamp_results = []
    for p in percentiles:
        index = int(len(timestamps) * p / 100.0)
        timestamp_results.append(timestamps[index])

    return timestamp_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot constructor")
    parser.add_argument("--benchmark", type=str, required=True)
    parser.add_argument(
        "--engine", type=str, required=True, choices=["pathway", "spark"]
    )
    parser.add_argument("--commit-frequency", type=int, required=True)
    parser.add_argument("--min-timestamp", type=int, default=0)
    parser.add_argument("--max-timestamp", type=int, default=sys.maxsize)
    parser.add_argument("--buckets", type=str)
    parser.add_argument("--shrink-first-lines", type=int, default=1000000)
    parser.add_argument("--shrink-first-milliseconds", type=int, default=2000)
    parser.add_argument(
        "--percentiles-for-plot", type=str, default="50,75,85,95,99,99.5"
    )
    args = parser.parse_args()

    buckets = set()
    percentiles = []
    if args.buckets:
        buckets = set([int(x) for x in args.buckets.split(",")])
    percentiles = [float(x) for x in args.percentiles_for_plot.split(",")]

    logs_root = os.path.join("..", "docker-compose", "results", args.engine)
    logs_list = os.listdir(logs_root)

    latest_timestamp: Dict[int, float] = {}
    logfile_per_timestamp: Dict[int, str] = {}
    for log_name in logs_list:
        if not log_name.startswith(args.benchmark):
            continue
        if not log_name.endswith("-timeline.txt"):
            continue

        log_name_parts = log_name.split("-")

        timestamp = float(log_name_parts[1])
        workers = int(log_name_parts[2])
        cores = int(log_name_parts[3])
        autocommit_frequency = int(log_name_parts[4])
        rate_per_second = int(log_name_parts[6])

        if autocommit_frequency != args.commit_frequency:
            continue
        if args.min_timestamp > timestamp or args.max_timestamp < timestamp:
            continue
        if latest_timestamp.get(rate_per_second, 0) > timestamp:
            continue
        latest_timestamp[rate_per_second] = timestamp
        logfile_per_timestamp[rate_per_second] = os.path.join(logs_root, log_name)
        if buckets and rate_per_second not in buckets:
            continue

    log_lines = []

    for rate_per_second, log_file_path in logfile_per_timestamp.items():
        percentile_values = read_timeline(
            log_file_path,
            args.shrink_first_lines,
            args.shrink_first_milliseconds,
            percentiles,
        )
        log_lines.append(
            ",".join([str(x) for x in [rate_per_second] + percentile_values])
        )

    log_lines.sort(key=lambda x: int(x.split(",")[0]))

    header = "rate_per_second," + ",".join(["p{}".format(x) for x in percentiles])
    csv_contents = header + "\n" + "\n".join(log_lines)
    print(csv_contents)
