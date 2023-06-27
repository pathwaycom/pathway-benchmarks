import argparse
from abc import ABC, abstractmethod

import pathway as pw  # type:ignore


class Benchmark(ABC):
    def __init__(self, autocommit_frequency_ms):
        self._autocommit_frequency_ms = autocommit_frequency_ms

    def get_rdkafka_settings(self):
        return {
            "group.id": "$GROUP_NAME",
            "bootstrap.servers": "kafka:9092",
            "enable.partition.eof": "false",
            "session.timeout.ms": "60000",
            "enable.auto.commit": "true",
            "queued.min.messages": "3000000",
        }

    @abstractmethod
    def run_benchmark(self):
        ...


class WordcountBenchmark(Benchmark):
    def get_input_table(self):
        return pw.io.kafka.read(
            rdkafka_settings=self.get_rdkafka_settings(),
            topic_names=["test_0"],
            format="json",
            value_columns=["word"],
            autocommit_duration_ms=self._autocommit_frequency_ms,
        )

    def output_table(self, table):
        return pw.io.kafka.write(
            table,
            rdkafka_settings=self.get_rdkafka_settings(),
            topic_name="test_1",
            format="dsv",
        )

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
    parser.add_argument("--autocommit-frequency-ms", type=int)
    parser.add_argument("--input-filename", type=str)
    args = parser.parse_args()

    autocommit_frequency = args.autocommit_frequency_ms or None

    benchmark = WordcountBenchmark(autocommit_frequency)
    benchmark.run_benchmark()
