import argparse
import subprocess
import time
from datetime import datetime

import psutil


def get_total_memory(p: psutil.Popen):
    max_memory = 0
    while p.poll() is None:
        try:
            children = p.children(recursive=True)
            current_memory = p.memory_info()[0]
            for child in children:
                current_memory += child.memory_info()[0]
            max_memory = max(max_memory, current_memory)
        except Exception:
            pass
        # print(len(children), p.memory_info()[0] / 1e9, current_memory / 1e9)
        time.sleep(0.5)
    return max_memory


def run(repeat, iterations, script_name, dataset, cores, memory):
    p = psutil.Popen(
        [
            "/opt/spark/bin/spark-submit",
            "--master",
            f"local[{cores}]",
            "--driver-memory",
            memory,  # 4g
            script_name,  # "spark_pagerank_4.py",
            dataset,  # "datasets/livejournal10_000.jl",
            str(iterations),
        ],
        stdout=subprocess.PIPE,
    )
    max_memory = get_total_memory(p)
    out, _ = p.communicate()
    total_time = out.decode("UTF-8").split("\n")[-2]
    with open(
        f"logs/{cores}_{dataset.split('/')[-1]}-{script_name}-{iterations}-{repeat}.csv",
        "w",
    ) as f:
        f.write(f"{max_memory},{total_time}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repeat", type=int, help="Repeat experiments this number of times"
    )
    parser.add_argument("--iterations", help="Comma separated list of iterations")
    parser.add_argument("--scripts", help="Comma separated list of scripts")
    parser.add_argument(
        "--datasets", help="Comma separated list of paths to the datasets"
    )
    parser.add_argument(
        "--cores",
        default=1,
        type=int,
        help="The number of cores to run spark on",
    )
    parser.add_argument("--memory", default="4g", help="Driver memory")

    args = parser.parse_args()

    iterations = [int(i) for i in args.iterations.split(",")]
    scripts = args.scripts.split(",")
    datasets = args.datasets.split(",")

    print(args.repeat, iterations, scripts, args.datasets)

    for r in range(args.repeat):
        for i in iterations:
            for script_name in scripts:
                for dataset in datasets:
                    print(datetime.now(), r, i, script_name, dataset)
                    run(r, i, script_name, dataset, args.cores, args.memory)
