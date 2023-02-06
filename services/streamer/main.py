import argparse
import subprocess
import time

PREPARED_DATASET_PATH = ".dataset-tmp"


class BenchmarkStreamer:
    def __init__(
        self, dataset_path, batch_size, rate_per_second, autocommit_frequency_ms
    ):
        self._dataset_path = dataset_path
        self._batch_size = batch_size
        self._rate_per_second = rate_per_second
        self._autocommit_frequency_ms = autocommit_frequency_ms

    def prepare_dataset_with_commits(self):
        # Prepare dataset
        with open(self._dataset_path, "r") as f, open(PREPARED_DATASET_PATH, "w") as fw:
            rows_in_batch = 0
            is_header = True
            for row in f:
                fw.write(row)
                if is_header:
                    is_header = False
                    continue
                rows_in_batch += 1
                if (
                    rows_in_batch == self._batch_size
                    and not self._autocommit_frequency_ms
                ):
                    fw.write("*COMMIT*\n")
                    rows_in_batch = 0

    def wait_for_engine_to_start(self):
        time.sleep(90)

    def run_streaming(self):
        self.prepare_dataset_with_commits()

        self.wait_for_engine_to_start()
        start_at = time.time()
        args = "cargo run -- {} {}".format(
            PREPARED_DATASET_PATH, self._rate_per_second
        ).split()
        popen = subprocess.Popen(args, stdout=subprocess.PIPE)
        popen.wait()
        finish_at = time.time()
        print("Time spent on streaming:", finish_at - start_at)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pathway benchmark streamer")
    parser.add_argument("--type", type=str, required=True)
    parser.add_argument("--dataset-path", type=str)
    parser.add_argument("--batch-size", type=int, default=10**9)
    parser.add_argument("--rate-per-second", type=int, default=10**6)
    parser.add_argument("--autocommit-frequency-ms", type=int)
    args = parser.parse_args()

    if args.type == "wordcount":
        dataset_path = args.dataset_path or "./datasets/wordcount-large.csv"
    elif args.type == "weighted_wordcount":
        dataset_path = args.dataset_path or "./datasets/weighted-wordcount-large.csv"
    elif args.type == "pagerank":
        dataset_path = args.dataset_path or "./datasets/pagerank.json"
    elif args.type == "increment":
        dataset_path = args.dataset_path or "./datasets/increment-large.json"
    else:
        raise RuntimeError("Unknown benchmark type: " + args.type)

    streamer = BenchmarkStreamer(
        dataset_path,
        args.batch_size,
        args.rate_per_second,
        args.autocommit_frequency_ms,
    )
    streamer.run_streaming()
