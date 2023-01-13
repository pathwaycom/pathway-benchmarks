# Pathway benchmarks

In this repository we provide a set of benchmarks of Pathway and a range of other similar technologies. 

## Repository organization

The top level of the repository contains a few directories:

- `docker-compose`, containing docker-compose files for running various benchmarks;
- `results`, containing aggregated results of the benchmarks in csv format;
- `services`, containing the Dockerized implementations of benchmarks along with auxiliary services required to stream dataset and to collect stats;
- `utils`, containing scripts for results collection and aggregation.

### `docker-compose`

This directory contains docker-compose files which execute in order to run the benchmark.

Normally, there is only one file required for running Pathway, which is `docker-compose-pathway.yml`. The image takes the benchmark type as well as other parameters from the environment variables, passed into its' containers through "environment" section (for example, [here](https://github.com/pathwaycom/IoT-Pathway/blob/sergey/benchmark-description/public/pathway-benchmarks/docker-compose/docker-compose-pathway.yml#L53)).

For other systems, there is usually a file for one pair of the benchmarked system and benchmark. For example, you can refer to the example benchmark of wordcount in Spark [here](https://github.com/pathwaycom/IoT-Pathway/blob/sergey/benchmark-description/public/pathway-benchmarks/docker-compose/docker-compose-spark-word-count.yml).

Since in benchmarks we basically want to compare multiple runs of one system with multiple runs of other system, we need to run these docker-compose images several times. For doing that in automated mode, there are simple `doall*.sh` files in the same directory. You can also refer to these files for the exemplary run commands of each benchmark.

### `results`

This directory contains the results of the test runs.

The top level of the directory contains three folders, corresponding to the benchmarks: `increment`, `pagerank` and `wordcount`. Each of the directory contains the runs data, named in the following format: `<system>-<type>.csv`. The system is basically one of the three compared systems. The type is either `unaware` for "batch-unaware" benchmarks or a number and denotes the size of the batch in the run of "batch-aware" benchmark. All non-Pathway runs are "batch-unaware".

### `services`

This directory contains the sevices, which are later organized into containers within docker-compose. The services are:

- `pathway-all`, implementation of all benchmarks in Pathway;
- `spark-word-count`, implementation of wordcount benchmark in Spark;
- `streamer`, service which streams the dataset into kafka at a given speed;
- `stats-collector`, service collecting the timeline of input and the output and calculating the run stats based on it.

### `utils`

Currently the directory contains only one script `collect_results.py`. The script fetches the data from the temporary directory `docker-compose/results` and organizes in the data into csv files in `results` directory.

## Benchmarks

There are three benchmarks, on which the comparison is made:

- `increment` benchmark reads a number from the input stream, increments it by one, and puts the increased number in the output stream;
- `wordcount` benchmark reads words from the stream and stores the count of each word in the output stream. For the sake of output compaction, only changed entries are streamed;
- `pagerank` benchmark gets graph edges from the input stream, computes pagerank of each node and streams it on the output;

## Benchmarked systems

In any benchmark, the following systems are compared to each other:

1. Pathway
2. Spark streaming
3. Kafka streams

### Two kinds of benchmarks for Pathway

One of Pathway features is that the user can manipulate the size of the batch, which is passed to the computational engine. For the sake of comparison, we have done a number of benchmarks, where we tried the different sizes of the batch. These benchmarks will be referred as "batch-aware", that is, the benchmarks where the user is aware of the batches and uses this split. 

On the other hand, the systems to which we compare, don't provide the same way to explicitly specify the end of the batch. In order to make the comparison fair, we also test Pathway in a mode, which accumulates the data into batches, based on clock time, in particularly, every 100 milliseconds. Since we don't explicitly terminate the batches here, we call these benchmarks "batch-unaware".

Respectively, all benchmarks of other systems are also "batch-unaware".

## Metrics used

There are two kinds of results, obtained as a result of benchmarking.

The first one reflects the total time spent on computation, based on the size of batch. It also shows the tradeoff between computing everything in a single piece and the realtime computation, based on the size of the batch of changes. 

The second one is a standardized comparison of end-to-end latencies. We denote the "end to end latency" as a difference between the last timestamp in the output stream and the last timestamp in the input stream. In a normally working system, that would be a nearly-constant time corresponding to the latency of processing a single message. The overloaded system, however, would not be able to process the stream of messages in a timely manner. So, eventually, it accumulates a queue of messages and replies with a delay. So, by this kind of metric we can judge of the throughput limits of a particular system. It should be noted that we also compute a number of proxy-metrics while performing benchmarks, but some of them only serve debug purposes.
