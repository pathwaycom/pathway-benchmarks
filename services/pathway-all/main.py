import argparse
import os

import pathway as pw
from pathway.internals import api, datasink, datasource, parse_graph
from pathway.internals._io_helpers import _form_value_fields
from pathway.internals.decorators import table_from_datasource
from pathway.internals.rustpy_builder import RustpyBuilder
from pathway.stdlib.graphs.pagerank import pagerank

KAFKA_PORT = 8192


class Benchmark:
    def __init__(self, autocommit_frequency_ms):
        self._autocommit_frequency_ms = autocommit_frequency_ms

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

    def construct_data_storage(self):
        return api.DataStorage(
            storage_type="kafka",
            rdkafka_settings=self.get_rdkafka_settings(),
            topics=["test_0"],
        )

    def run_benchmark(self):
        raise NotImplementedError("You need to implement calculations for benchmark")


class PagerankBenchmark(Benchmark):
    def run_benchmark(self):
        data_storage = self.construct_data_storage()
        data_format = api.DataFormat(
            format_type="jsonlines",
            key_field_names=["id"],
            value_fields=_form_value_fields(["id"], ["u", "v"]),
        )
        edges_getter = table_from_datasource(
            datasource.GenericDataSource(
                data_storage,
                data_format,
                self._autocommit_frequency_ms,
            )
        )
        edges = edges_getter.select(
            u=edges_getter.pointer_from(pw.this.u),
            v=edges_getter.pointer_from(pw.this.v),
        )
        result = pagerank(edges, 5)

        data_storage = api.DataStorage(
            storage_type="kafka",
            rdkafka_settings=self.get_rdkafka_settings(),
            topics=["test_1"],
        )
        data_format = api.DataFormat(
            format_type="dsv",
            key_field_names=[],
            value_fields=_form_value_fields([], ["rank"]),
            delimiter=",",
        )
        result.to(
            datasink.GenericDataSink(
                data_storage,
                data_format,
            )
        )

        RustpyBuilder(parse_graph.G).run_outputs()


class WordcountBenchmark(Benchmark):
    def run_benchmark(self):
        data_storage = self.construct_data_storage()
        data_format = api.DataFormat(
            format_type="jsonlines",
            key_field_names=None,
            value_fields=_form_value_fields(None, ["word"], None),
        )
        words = table_from_datasource(
            datasource.GenericDataSource(
                data_storage,
                data_format,
                self._autocommit_frequency_ms,
            )
        )

        result = words.groupby(words.word).reduce(
            words.word,
            count=pw.reducers.count(),
        )

        data_storage = api.DataStorage(
            storage_type="kafka",
            rdkafka_settings=self.get_rdkafka_settings(),
            topics=["test_1"],
        )
        data_format = api.DataFormat(
            format_type="dsv",
            key_field_names=[],
            value_fields=_form_value_fields([], ["word", "count"], None),
            delimiter=",",
        )
        result.to(
            datasink.GenericDataSink(
                data_storage,
                data_format,
            )
        )

        RustpyBuilder(parse_graph.G).run_outputs()


class WeightedWordcountBenchmark(Benchmark):
    def run_benchmark(self):
        data_storage = self.construct_data_storage()
        data_format = api.DataFormat(
            format_type="jsonlines",
            key_field_names=None,
            value_fields=_form_value_fields(None, ["word", "weight"], None),
        )
        words = table_from_datasource(
            datasource.GenericDataSource(
                data_storage,
                data_format,
                self._autocommit_frequency_ms,
            )
        )

        result = words.groupby(words.word).reduce(
            words.word,
            count=pw.reducers.sum(words.weight),
        )

        data_storage = api.DataStorage(
            storage_type="kafka",
            rdkafka_settings=self.get_rdkafka_settings(),
            topics=["test_1"],
        )
        data_format = api.DataFormat(
            format_type="dsv",
            key_field_names=[],
            value_fields=_form_value_fields([], ["word", "count"]),
            delimiter=",",
        )
        result.to(
            datasink.GenericDataSink(
                data_storage,
                data_format,
            )
        )

        RustpyBuilder(parse_graph.G).run_outputs()


class IncrementBenchmark(Benchmark):
    def run_benchmark(self):
        numbers = pw.kafka.read(
            rdkafka_settings=self.get_rdkafka_settings(),
            topic_names=["test_0"],
            format="json",
            value_columns=["number"],
            types={
                "number": pw.Type.INT,
            },
            autocommit_duration_ms=self._autocommit_frequency_ms,
        )

        result = numbers.select(number=pw.this.number).select(
            increased_number=pw.this.number + 1
        )

        data_storage = api.DataStorage(
            storage_type="kafka",
            rdkafka_settings=self.get_rdkafka_settings(),
            topics=["test_1"],
        )
        data_format = api.DataFormat(
            format_type="dsv",
            key_field_names=[],
            value_fields=_form_value_fields([], ["increased_number"]),
            delimiter=",",
        )
        result.to(
            datasink.GenericDataSink(
                data_storage,
                data_format,
            )
        )

        RustpyBuilder(parse_graph.G).run_outputs()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pathway benchmarker")
    parser.add_argument("--type", type=str, required=True)
    parser.add_argument("--autocommit-frequency-ms", type=int)
    args = parser.parse_args()

    autocommit_frequency = args.autocommit_frequency_ms or None

    if args.type == "wordcount":
        benchmark: Benchmark = WordcountBenchmark(autocommit_frequency)
    elif args.type == "weighted_wordcount":
        benchmark = WeightedWordcountBenchmark(autocommit_frequency)
    elif args.type == "pagerank":
        benchmark = PagerankBenchmark(autocommit_frequency)
    elif args.type == "increment":
        benchmark = IncrementBenchmark(autocommit_frequency)
    else:
        raise RuntimeError("Unknown benchmark type: " + args.type)

    benchmark.run_benchmark()
