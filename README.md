# Pathway benchmarks

In this repository, we provide a set of benchmarks of Pathway and a range of other similar technologies. 

## Benchmarks

There are two benchmarks, on which the comparison is made:

- Wordcount benchmark reads words from the stream and stores the count of each word in the output stream. For the sake of output compaction, only changed entries are streamed. In this kind of benchmark, Kafka is used for input and output;
- Pagerank benchmark gets graph edges from the input stream, computes the PageRank of each node, and streams it on the output. In this kind of benchmark, filesystem input and empty output are used;

## Repository organization

The top level of the repository contains a few directories. The most important ones are:

- `docker-compose`, containing docker-compose files for running various benchmarks;
- `services`, containing the Dockerized implementations of benchmarks along with auxiliary services required to stream datasets and to collect stats;

### `docker-compose`

This directory contains docker-compose files which execute in order to run the benchmarks.

Normally, only one file is required for running Pathway, which is `docker-compose-pathway.yml`. The image takes the benchmark type as well as other parameters from the environment variables and passed them into its' containers through the "environment" section.

For other systems, there is usually a file for one pair of the benchmarked system and benchmark.

Since in benchmarks we basically want to compare multiple runs of one system with multiple runs of other systems, we need to run these docker-compose images several times. There is a `run_wordcount.py` file in the directory for doing that in automated mode.

### `services`

This directory contains the services, which are later organized into containers within docker-compose. Some of the services are auxiliary and don't perform any benchmarked computations. These services are:

- `streamer`, which streams the dataset into Kafka at a given speed;
- `stats-collector`, collecting the timeline of input and the output and calculating the run stats based on it.

Some services are dedicated to running a benchmark in a specific system. For instance:

- `pathway-all`, implementing Wordcount and Pagerank benchmarks in Pathway. This directory also contains the Python script for running Pagerank benchmark in Python;
- `flink-pagerank`, implementing batch scenario of Pagerank in Flink;
- `flink-pagerank-streaming`, implementing streaming scenario of Pagerank in Flink;
- `spark-pagerank-graphx`, implementing Pagerank in Spark GraphX;
- `spark-pagerank`, implementing Pagerank in Spark (without the usage of GraphX);
- `flink-word-count` and `flink-word-count-minibatch`, implementing two various versions of Wordcount in Flink;
- `spark-word-count`, implementing Wordcount in Spark.
