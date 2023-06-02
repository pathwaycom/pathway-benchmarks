import argparse
import os
import platform
import subprocess
import warnings

LINUX_LAUNCH_COMMAND = "taskset --cpu-list {} python {} --input-filename {} --pagerank-steps {}"  # noqa: E501
OTHER_LAUNCH_COMMAND = "python {} --input-filename {} --pagerank-steps {}"  # noqa: E501


def get_launch_command(path, cpu_list, input_filename, pagerank_steps):
    if platform.system() != "Linux":
        warnings.warn(
            "The OS is not Linux, unable to restrict used CPU cores to a certain set"
        )
        return OTHER_LAUNCH_COMMAND.format(path, input_filename, pagerank_steps)
    else:
        return LINUX_LAUNCH_COMMAND.format(
            cpu_list, path, input_filename, pagerank_steps
        )


def taskset_string(cpu_pool, n_cpus):
    return ",".join(str(cpu_id) for cpu_id in cpu_pool[: min(n_cpus, len(cpu_pool))])


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
        os.environ["PATHWAY_THREADS"] = str(n_cpus)  # Restict computational cores
        for n_steps in n_steps_to_test:
            path = "/".join(os.path.abspath(__file__).split("/")[:-1]) + "/main.py"
            command = get_launch_command(
                path,
                taskset_string(available_core_ids, n_cpus),
                dataset_path,
                n_steps,
            )
            run_args = command.split()

            for n_repeat in range(n_repeats):
                print("Executing...", run_args)

                popen = subprocess.Popen(run_args, stdout=subprocess.PIPE)
                popen.wait()
