import os
import signal
import subprocess
import time
from functools import partial

throughputs = [x for x in range(200000, 1200001, 100000)]
pw_throughputs = [x for x in range(200000, 1200001, 100000)]
pw_batch_size_ms = [20, 100]
batch_size_ms = [20, 100]

dict_sizes = [5000]

DATASET_WARMUP_PREFIX_LENGTH = 16000000
RECORDED_DATASET_SIZE = 60000000

STREAMER_WAIT_TIME_MS = 25000
STREAMER_EMIT_INTERVAL_MS = 8


REPS = 1
non_batched_engines = ["flink"]
# non_batched_engines = []  # type:ignore
batched_engines = ["flink_minibatching", "kstreams", "spark"]
# batched_engines = []  # type:ignore
pw_engines = ["pathway"]

cores = [2, 4]

tested_cpu_map = {
    1: "0",
    2: "0-1",
    4: "0-3",
    6: "0-5",
    8: "0-7",
}

harness_cpu_map = {
    1: "8-11",
    2: "8-11",
    4: "8-11",
    6: "8-11",
    8: "8-11",
}

docker_compose_map = {
    "pathway": "pathway",
    "flink": "flink-word-count-local",
    "flink_minibatching": "flink-word-count-local-minibatch",
    "kstreams": "kafka-streams",
    "spark": "spark-word-count-scala-local",
}


def run_record(up_command, down_command, resources_stats_command):
    # unwrap mappings from iterated values
    up_command = up_command.format(
        tested_cpu_map=tested_cpu_map,
        harness_cpu_map=harness_cpu_map,
        cores=cores,
        docker_compose_map=docker_compose_map,
    )

    res = subprocess.Popen(resources_stats_command, shell=True, preexec_fn=os.setsid)

    run = subprocess.Popen(up_command, shell=True)
    run.wait()

    clean = subprocess.Popen(down_command, shell=True)
    clean.wait()

    os.killpg(os.getpgid(res.pid), signal.SIGTERM)


def fetch_commit_number():
    return (
        subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
        .decode("ascii")
        .strip()
    )


# the general idea is to have a function that
# - takes list of the lists,
# - iterates over the head-list, partially evaluating format on the command_template
# - calls itself recursively

# This allows us to easily modify the ordering / number of the for loops in a test scenario
# Also, in case something needs to be iterated by hand, we can also add some for loops
# that happen on the outside, feed the recursive function partially set command


def iterate_over_runs(partial_up_command, down_command, res_command, ranges):
    if len(ranges) == 0:
        return run_record(partial_up_command(), down_command, res_command)
    head, *tail = ranges

    for value in head:
        iterate_over_runs(
            partial(partial_up_command, value), down_command, res_command, tail
        )


def main():
    version_prefix = f"CODE_VERSION={fetch_commit_number()} "
    record_size = f"RECORDED_DATASET_SIZE={RECORDED_DATASET_SIZE} "
    skip_pref = f"DATASET_WARMUP_PREFIX_LENGTH={DATASET_WARMUP_PREFIX_LENGTH} "
    streamer_wait_time = f"STREAMER_WAIT_TIME_MS={STREAMER_WAIT_TIME_MS} "
    streamer_emit_interval = f"STREAMER_EMIT_INTERVAL_MS={STREAMER_EMIT_INTERVAL_MS} "

    up_command_template = (
        version_prefix
        + skip_pref
        + record_size
        + streamer_wait_time
        + streamer_emit_interval
        + "ENGINE_TYPE={0} "
        + "RATE_PER_SECOND={1} "
        + "AUTOCOMMIT_FREQUENCY_MS={2} "
        + "CORES={3} "
        + "TESTED_CPU_SET={{tested_cpu_map[{3}]}} "
        + "HARNESS_CPU_SET={{harness_cpu_map[{3}]}} "
        + "docker-compose -p $USER "
        + "--env-file variables_ext.env "
        + "-f docker-compose-{{docker_compose_map[{0}]}}.yml "
        + "up stats-collector> {0}_log.txt>&1 --build"
    )
    down_command = "docker-compose -p $USER down -v --remove-orphans"

    subprocess.Popen("mkdir run_resources", shell=True)
    res_command = (
        "taskset -c 6 docker stats --format "
        + '"table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" '
        + f"> run_resources/{time.time()}_service_stats_log.txt"
    )

    # Below, we iterate over reps and dict-sizes outside of the function, as:
    # - reps do not go into the command (albeit one could add some comment at the end that
    # collects this kind of unused parameters, and it's fine to have them as outermost-loop
    # - going through dict_size requires to generate the dataset,
    # - - it would be somewhat inconvenient (but not impossible) to do it in the recursive function
    # - - we want to generate it once, and use for all the tests; even though it is
    # generated with pseudorandomness, just waiting to re-generate the dataset for each
    # testcase would add quite a long time

    for rep in range(REPS):
        for dsize in dict_sizes:

            dict_size_pref = f"DICT_SIZE={dsize} "
            testgen_cmd = (
                "python ../services/streamer/datasets/wordcount-large-gen.py "
                + f"--dict-size {dsize} "
                + f"--dataset-size {DATASET_WARMUP_PREFIX_LENGTH + RECORDED_DATASET_SIZE}"
            )
            subprocess.Popen(testgen_cmd, shell=True).wait()

            cp_cmd = "cp ./wordcount-large.csv ../services/streamer/datasets/"
            subprocess.Popen(cp_cmd, shell=True).wait()

            iterate_over_runs(
                (dict_size_pref + up_command_template).format,
                down_command,
                res_command,
                [pw_engines, pw_throughputs, pw_batch_size_ms, cores],
            )


if __name__ == "__main__":
    main()
