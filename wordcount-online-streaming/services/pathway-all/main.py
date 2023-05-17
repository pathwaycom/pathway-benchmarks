import argparse
import os
from abc import ABC, abstractmethod

import pathway as pw  # type:ignore
from pathway.stdlib.graphs.pagerank import pagerank  # type:ignore


class Benchmark(ABC):
    def __init__(
        self, autocommit_frequency_ms, channel, input_filename, *args, **kwargs
    ):
        self._autocommit_frequency_ms = autocommit_frequency_ms
        self._channel = channel
        self._input_filename = input_filename

    def get_rdkafka_settings(self):
        using_benchmark_harness = os.environ.get("USING_BENCHMARK_HARNESS") == "1"
        bootstrap_server = "kafka:9092" if using_benchmark_harness else "localhost:9092"
        return {
            "group.id": "$GROUP_NAME",
            "bootstrap.servers": bootstrap_server,
            "enable.partition.eof": "false",
            "session.timeout.ms": "60000",
            "enable.auto.commit": "true",
            "queued.min.messages": "3000000",
        }

    @abstractmethod
    def run_benchmark(self):
        ...


class PagerankBenchmark(Benchmark):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pagerank_steps = kwargs.get("pagerank_steps", 5)

    def get_input_table(self):
        if self._channel == "fs":
            return pw.io.jsonlines.read(
                path=self._input_filename,
                mode="static",
                primary_key=None,
                value_columns=["u", "v"],
                types={
                    "u": pw.Type.INT,
                    "v": pw.Type.INT,
                },
            )
        elif self._channel == "kafka":
            raise NotImplementedError(
                "For Pagerank benchmark, only file IO is supported"
            )
        else:
            raise ValueError("Unknown data channel: {}".format(self._channel))

    def run_benchmark(self):
        input_table = self.get_input_table()
        edges = input_table.select(
            u=input_table.pointer_from(pw.this.u),
            v=input_table.pointer_from(pw.this.v),
        )
        print("Launching pagerank with {} steps...".format(self.pagerank_steps))
        result = pagerank(edges, self.pagerank_steps)
        pw.io.null.write(result)
        pw.run()


class WordcountBenchmark(Benchmark):
    def get_input_table(self):
        if self._channel == "fs":
            return pw.io.jsonlines.read(
                path=self._input_filename,
                poll_new_objects=False,
                primary_key=None,
                value_columns=["word"],
            )
        elif self._channel == "kafka":
            return pw.io.kafka.read(
                rdkafka_settings=self.get_rdkafka_settings(),
                topic_names=["test_0"],
                format="json",
                value_columns=["word"],
                autocommit_duration_ms=self._autocommit_frequency_ms,
            )
        else:
            raise ValueError("Unknown data channel: {}".format(self._channel))

    def output_table(self, table):
        if self._channel == "fs":
            return pw.io.null.write(table)
        elif self._channel == "kafka":
            return pw.io.kafka.write(
                table,
                rdkafka_settings=self.get_rdkafka_settings(),
                topic_name="test_1",
                format="dsv",
            )
        else:
            raise ValueError("Unknown data channel: {}".format(self._channel))

    def run_benchmark(self):
        words = self.get_input_table()
        result = words.groupby(words.word).reduce(
            words.word,
            count=pw.reducers.count(),
        )
        self.output_table(result)
        pw.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pathway benchmarker")
    parser.add_argument("--type", type=str, required=True)
    parser.add_argument("--autocommit-frequency-ms", type=int)
    parser.add_argument("--channel", type=str, default="kafka", choices=["kafka", "fs"])
    parser.add_argument("--input-filename", type=str)
    parser.add_argument("--pagerank-steps", type=int, default=5)
    args = parser.parse_args()

    autocommit_frequency = args.autocommit_frequency_ms or None

    if args.type == "wordcount":
        benchmark: Benchmark = WordcountBenchmark(
            autocommit_frequency, args.channel, args.input_filename
        )
    else:
        raise RuntimeError("Unknown benchmark type: " + args.type)
    benchmark.run_benchmark()