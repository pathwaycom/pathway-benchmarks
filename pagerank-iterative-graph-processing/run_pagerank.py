import os
import subprocess

DATASET_NAMES = [
    "datasets/pagerank-400k-batch.jsonlines",
    "datasets/pagerank-400k-streaming.jsonlines",
    "datasets/pagerank-5m-batch.jsonlines",
    "datasets/pagerank-5m-streaming.jsonlines",
    "datasets/pagerank-5m-backfilling.jsonlines",
    "datasets/pagerank-full.jsonlines",
    "datasets/pagerank-full-one.jsonlines",
]


def run_flink_benchmark():
    flink_path = os.path.dirname(os.path.realpath(__file__)) + "/pagerank_flink"

    # run
    run_command = flink_path + "/flink_pagerank_all_final.sh"
    subprocess.call(["sh", run_command], cwd=flink_path)

    # collect and print results
    run_command = flink_path + "/flink_pagerank_all_final_get_stats.sh"
    subprocess.call(["sh", run_command], cwd=flink_path)


if __name__ == "__main__":
    os.system("docker build -t pagerank_pathway -f pagerank_pathway/Dockerfile .")

    for dataset_name in DATASET_NAMES:
        run_command = "docker run -e 'DATASET_PATH={}' -e 'AVAILABLE_CORE_IDS=0,1,2,3,4,5' -e 'N_CORES_TO_TEST=1,2,4,6' -e 'N_STEPS_TO_TEST=5' -e 'REPEATS=5' pagerank_pathway".format(  # noqa: E501
            dataset_name
        )
        os.system(run_command)

    run_flink_benchmark()
