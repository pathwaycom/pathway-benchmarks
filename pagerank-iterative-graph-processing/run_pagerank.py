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
    for dataset_name in DATASET_NAMES:
        run_command = "python pagerank_pathway/doall.py --dataset-path {} --available-core-ids 0,1,2,3,4,5 --n-cores-to-test 1,2,4 --n-steps-to-test 5 --repeats 3".format(  # noqa: E501
            dataset_name
        )
        run_args = run_command.split()
        popen = subprocess.Popen(run_args, stdout=subprocess.PIPE)
        popen.wait()

    run_flink_benchmark()
