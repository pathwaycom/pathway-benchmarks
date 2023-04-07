import argparse
import os
import subprocess

BASE_LAUNCH_COMMAND = "taskset --cpu-list {} python main.py --type pagerank --autocommit-frequency-ms 1000000000 --channel fs --input-filename {} --pagerank-steps {}"  # noqa: E501


def taskset_string(cpu_pool, n_cpus):
    return ",".join(
        str(cpu_id) for cpu_id in cpu_pool[: min(n_cpus + 1, len(cpu_pool))]
    )


def parse_args_list(raw_repr):
    return [int(x) for x in raw_repr.strip().split(",")]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch and backfilling experiments coordinator"
    )
    parser.add_argument("--dataset-path", type=str, required=True)
    parser.add_argument("--available-core-ids", type=str, required=True)
    parser.add_argument("--n-cores-to-test", type=str, required=True)
    parser.add_argument("--n-steps-to-test", type=str, default="5")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    os.environ["PATHWAY_YOLO_RARE_WAKEUPS"] = "1"
    os.environ["PATHWAY_PROFILE"] = "release"
    os.environ["PATHWAY_IGNORE_ASSERTS"] = "1"

    available_core_ids = parse_args_list(args.available_core_ids)
    n_cores_to_test = parse_args_list(args.n_cores_to_test)
    n_steps_to_test = parse_args_list(args.n_steps_to_test)
    n_repeats = args.repeats
    dataset_path = args.dataset_path

    for n_cpus in n_cores_to_test:
        os.environ["PATHWAY_THREADS"] = str(n_cpus)
        for n_steps in n_steps_to_test:
            command = BASE_LAUNCH_COMMAND.format(
                taskset_string(available_core_ids, n_cpus),
                dataset_path,
                n_steps,
            )
            args = command.split()

            for n_repeat in range(n_repeats):
                print("Executing...", args)

                popen = subprocess.Popen(args, stdout=subprocess.PIPE)
                popen.wait()
