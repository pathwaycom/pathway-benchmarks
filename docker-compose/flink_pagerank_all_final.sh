#!/bin/bash

# Before running this script, make sure that:
# - /services/flink-pagerank/pagerank/data contains:
#   * livejournal.json              (full live)
#   * livejournal_truncated.json    (first 5M edges)
#   * livejournal_400.json          (first 400k edges)

# - /services/flink-pagerank-streaming/pagerank/data contains:
#   * livejournal_truncated.json
#   * livejournal_400.json

rundate="2023-04-22"
iterations=5

for try in {1..5}
do
    # batch benchmark
    for dataset in "livejournal_400" "livejournal_truncated" "livejournal"
    do
        for parallelism in 1 2 4 6
        do
            cpusetmin=0
            cpusetmax=$(( parallelism - 1 ))      
            docker-compose -p $USER -f flink-pagerank-local.yml down -v
            TESTED_CPU_SET="$cpusetmin-$cpusetmax" PARALLELISM=$parallelism PAGERANK_ITERATIONS=$iterations INPUT_FILENAME=$dataset.json docker-compose -p $USER -f flink-pagerank-local.yml up > pagerank-flink-results/batch/result-$rundate-$dataset-$parallelism-$iterations-$try.txt
        done
    done

    # streaming benchmarks - 1000 commit size
    minibatch=1000

    # A) no backfill
    backfill=0
    for dataset in "livejournal_400" # "livejournal_truncated" - this (5M) would take a while using all memory, please run separately
    do
        for parallelism in 1 2 4 6
        do
            cpusetmin=0
            cpusetmax=$(( parallelism - 1 ))
            docker-compose -p $USER -f flink-pagerank-local-streaming.yml down -v
            TESTED_CPU_SET="$cpusetmin-$cpusetmax" BACKFILL=$backfill BATCH_SIZE=100000000 ALLOW_LATENCY=$minibatch PARALLELISM=$parallelism PAGERANK_ITERATIONS=$iterations INPUT_FILENAME=$dataset.json docker-compose -p $USER -f flink-pagerank-local-streaming.yml up > pagerank-flink-results/streaming/result-nobackfill-$rundate-$dataset-$parallelism-$iterations-$try.txt
        done
    done

    # B) backfill 4.5M
    backfill=4500000
    for dataset in "livejournal_truncated"
    do
        for parallelism in 1 2 4 6
        do
            cpusetmin=0
            cpusetmax=$(( parallelism - 1 ))
            docker-compose -p $USER -f flink-pagerank-local-streaming.yml down -v
            # parallelism set to 6 to avoid hitting minibatch buffers
            TESTED_CPU_SET="$cpusetmin-$cpusetmax" BACKFILL=$backfill BATCH_SIZE=100000000 ALLOW_LATENCY=$minibatch PARALLELISM=6 PAGERANK_ITERATIONS=$iterations INPUT_FILENAME=$dataset.json docker-compose -p $USER -f flink-pagerank-local-streaming.yml up > pagerank-flink-results/streaming/result-backfill-4.5M-$rundate-$dataset-$parallelism-$iterations-$try.txt
        done
    done

    # C) backfill 4999999
    backfill=4999999
    for dataset in "livejournal_truncated"
    do
        for parallelism in 1 2 4 6
        do
            cpusetmin=0
            cpusetmax=$(( parallelism - 1 ))
            docker-compose -p $USER -f flink-pagerank-local-streaming.yml down -v
            # parallelism set to 6 to avoid hitting minibatch buffers
            TESTED_CPU_SET="$cpusetmin-$cpusetmax" BACKFILL=$backfill BATCH_SIZE=100000000 ALLOW_LATENCY=$minibatch PARALLELISM=6 PAGERANK_ITERATIONS=$iterations INPUT_FILENAME=$dataset.json docker-compose -p $USER -f flink-pagerank-local-streaming.yml up > pagerank-flink-results/streaming/result-backfill-4999999-$rundate-$dataset-$parallelism-$iterations-$try.txt
        done
    done

done