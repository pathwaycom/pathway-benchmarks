import os
import subprocess

CPUS = [1, 2, 4, 6, 8, 10, 12]
PR_STEPS = [1, 2, 5, 10, 20]
N_REPEATS = 5

BASE_LAUNCH_COMMAND = "taskset --cpu-list {} python main.py --type pagerank --autocommit-frequency-ms 1000000000 --channel fs --input-filename ../streamer/datasets/pagerank-5m-backfill.json --pagerank-steps {}"  # noqa: E501


def taskset_string(n_cpus):
    cpu_ids = []
    for i in range(n_cpus):
        cpu_ids.append(str(i))
    return ",".join(cpu_ids)


if __name__ == "__main__":
    os.environ["PATHWAY_YOLO_RARE_WAKEUPS"] = "1"
    os.environ["PATHWAY_PROFILE"] = "release"
    for n_cpus in CPUS:
        os.environ["PATHWAY_THREADS"] = str(n_cpus)
        for n_steps in PR_STEPS:
            for n_repeat in range(N_REPEATS):
                command = BASE_LAUNCH_COMMAND.format(taskset_string(n_cpus), n_steps)

                args = command.split()
                print("Executing...", args)

                popen = subprocess.Popen(args, stdout=subprocess.PIPE)
                popen.wait()
