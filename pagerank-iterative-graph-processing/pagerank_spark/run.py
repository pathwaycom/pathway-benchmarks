import argparse
import logging
import os
import subprocess
import time

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
        time.sleep(0.5)
    return max_memory


def run(repeat, iterations, script_name, dataset, cores, memory):
    p = psutil.Popen(
        [
            "/opt/spark/bin/spark-submit",
            "--master",
            f"local[{cores}]",
            "--driver-memory",
            memory,
            script_name,
            dataset,
            str(iterations),
        ],
        stdout=subprocess.PIPE,
    )
    max_memory = get_total_memory(p)
    out, _ = p.communicate()
    total_time = out.decode("UTF-8").split("\n")[-2]
    os.makedirs("/results/", exist_ok=True)
    with open(
        f"/results/spark-{cores}_{dataset.split('/')[-1]}-{script_name}-{iterations}-{repeat}.csv",
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

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s]:%(levelname)s:%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    logging.info(f"{args.repeat}, {iterations}, {scripts}, {args.datasets}")

    for r in range(args.repeat):
        for i in iterations:
            for script_name in scripts:
                for dataset in datasets:
                    logging.info(
                        f"repeat no.: {r}, iterations: {i}, {script_name}, {dataset}"
                    )
                    run(r, i, script_name, dataset, args.cores, args.memory)
