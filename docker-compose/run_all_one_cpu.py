import os
import signal
import subprocess

throughputs = [x for x in range(100000, 850001, 50000)]
pw_throughputs = [x for x in range(100000, 850001, 50000)]
pw_batch_size_ms = [5, 10, 20, 50, 100]
batch_size_ms = [20, 100]

dict_sizes = [5000]
REPS = 2
non_batched_engines = ["flink"]
batched_engines = ["flink_minibatching", "kstreams", "spark"]
pw_engines = ["pathway"]

tested_cpu_map = {
    0: "0",
    1: "6",
    2: "1",
    3: "7",
    4: "2",
    5: "8",
    6: "3",
    7: "9",
    8: "4",
    9: "10",
    10: "5",
    11: "11",
}

harness_cpu_map = {
    0: "9-11",
    1: "3-5",
    2: "9-11",
    3: "3-5",
    4: "9-11",
    5: "3-5",
    6: "6-8",
    7: "0-2",
    8: "6-8",
    9: "0-2",
    10: "6-8",
    11: "0-2",
}

docker_compose_map = {
    "pathway": "pathway",
    "flink": "flink-word-count-local",
    "flink_minibatching": "flink-word-count-local-minibatch",
    "kstreams": "kafka-streams",
    "spark": "spark-word-count-scala-local",
}


def run_record(up_command, down_command, resources_stats_command):
    # res_cmd_list = resources_stats_command.split()
    res = subprocess.Popen(resources_stats_command, shell=True, preexec_fn=os.setsid)

    # up_cmd_list = up_command.split()
    run = subprocess.Popen(up_command, shell=True)
    run.wait()

    # down_cmd_list = down_command.split()
    clean = subprocess.Popen(down_command, shell=True)
    clean.wait()

    os.killpg(os.getpgid(res.pid), signal.SIGTERM)


def main():
    test_cnt = -1
    up_command_template = (
        "ENGINE_TYPE={0} "
        + "RATE_PER_SECOND={1} "
        + "DICT_SIZE={2} "
        + "AUTOCOMMIT_FREQUENCY_MS={3} "
        + "TESTED_CPU_SET={4} "
        + "HARNESS_CPU_SET={5} "
        + "docker-compose -p $USER "
        + "--env-file variables_ext.env "
        + "-f docker-compose-{6}.yml "
        + "up stats-collector> {7}_log.txt>&1 --build"
    )
    down_command = "docker-compose -p $USER down -v --remove-orphans"

    subprocess.Popen("mkdir run_resources", shell=True)
    res_command_template = (
        "taskset -c 6 docker stats --format "
        + '"table {{{{.Name}}}}\t{{{{.CPUPerc}}}}\t{{{{.MemUsage}}}}" '
        + "> run_resources/{0}_{1}_{2}_{3}_{4}_service_stats_log.txt"
    )

    for dsize in dict_sizes:
        testgen_cmd = (
            "python ../services/streamer/datasets/wordcount-large-gen.py "
            + f"--dict-size {dsize}"
        )
        subprocess.Popen(testgen_cmd, shell=True).wait()

        cp_cmd = "cp ./wordcount-large.csv ../services/streamer/datasets/"
        subprocess.Popen(cp_cmd, shell=True).wait()

        for rep in range(REPS):
            for engine in pw_engines:
                for throughput in pw_throughputs:
                    for bsize in pw_batch_size_ms:
                        test_cnt += 1
                        up_command = up_command_template.format(
                            engine,
                            throughput,
                            dsize,
                            bsize,
                            tested_cpu_map[test_cnt % 12],
                            harness_cpu_map[test_cnt % 12],
                            docker_compose_map[engine],
                            engine,
                        )
                        res_command = res_command_template.format(
                            engine, dsize, throughput, bsize, rep
                        )
                        run_record(up_command, down_command, res_command)

            for engine in batched_engines:
                for throughput in throughputs:
                    for bsize in batch_size_ms:
                        test_cnt += 1
                        up_command = up_command_template.format(
                            engine,
                            throughput,
                            dsize,
                            bsize,
                            tested_cpu_map[test_cnt % 12],
                            harness_cpu_map[test_cnt % 12],
                            docker_compose_map[engine],
                            engine,
                        )
                        res_command = res_command_template.format(
                            engine, dsize, throughput, bsize, rep
                        )
                        run_record(up_command, down_command, res_command)

            for engine in non_batched_engines:
                for throughput in throughputs:
                    test_cnt += 1
                    up_command = up_command_template.format(
                        engine,
                        throughput,
                        dsize,
                        1,
                        tested_cpu_map[test_cnt % 12],
                        harness_cpu_map[test_cnt % 12],
                        docker_compose_map[engine],
                        engine,
                    )
                    res_command = res_command_template.format(
                        engine, dsize, throughput, 1, rep
                    )
                    run_record(up_command, down_command, res_command)


if __name__ == "__main__":
    main()
