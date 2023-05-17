import argparse
import subprocess
import sys
import time

PREPARED_DATASET_PATH = ".dataset-tmp"


class BenchmarkStreamer:
    def __init__(
        self,
        dataset_path,
        batch_size,
        rate_per_second,
        autocommit_frequency_ms,
        skip_prefix_length,
        wait_time_ms,
        emit_interval_ms,
    ):
        self._dataset_path = dataset_path
        self._batch_size = batch_size
        self._rate_per_second = rate_per_second
        self._autocommit_frequency_ms = autocommit_frequency_ms
        self._skip_prefix_length = skip_prefix_length
        self._wait_time_ms = wait_time_ms
        self._emit_interval_ms = emit_interval_ms

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
        print("streamer starting", file=sys.stderr)
        self.prepare_dataset_with_commits()

        self.wait_for_engine_to_start()
        print("streamer done waiting", file=sys.stderr)
        start_at = time.time()
        args_f = (
            "target/release/streamer "
            + "--dataset-path {0} "
            + "--messages-per-second {1} "
            + "--skip-prefix-length {2} "
            + "--wait-time-ms {3} "
            + "--emit-interval-ms {4} "
        )

        args = args_f.format(
            PREPARED_DATASET_PATH,
            self._rate_per_second,
            self._skip_prefix_length,
            self._wait_time_ms,
            self._emit_interval_ms,
        ).split()

        print("running ", args, file=sys.stderr)
        popen = subprocess.Popen(args, stdout=subprocess.PIPE)
        popen.wait()
        finish_at = time.time()
        print("Time spent on streaming:", finish_at - start_at, file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pathway benchmark streamer")
    parser.add_argument("--type", type=str, required=True)
    parser.add_argument("--dataset-path", type=str)
    parser.add_argument("--batch-size", type=int, default=10**9)
    parser.add_argument("--rate-per-second", type=int, default=10**6)
    parser.add_argument("--autocommit-frequency-ms", type=int)
    parser.add_argument("--skip-prefix-length", type=int, default=0)
    parser.add_argument("--wait-time-ms", type=int, default=0)
    parser.add_argument("--emit-interval-ms", type=int, default=0)
    args = parser.parse_args()

    if args.type == "wordcount":
        dataset_path = args.dataset_path or "./datasets/wordcount-large.csv"
    elif args.type == "pagerank":
        dataset_path = args.dataset_path or "./datasets/pagerank.json"
    else:
        raise RuntimeError("Unknown benchmark type: " + args.type)

    streamer = BenchmarkStreamer(
        dataset_path,
        args.batch_size,
        args.rate_per_second,
        args.autocommit_frequency_ms,
        args.skip_prefix_length,
        args.wait_time_ms,
        args.emit_interval_ms,
    )
    streamer.run_streaming()
