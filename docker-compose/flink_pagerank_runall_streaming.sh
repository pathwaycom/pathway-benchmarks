#!/bin/bash

for try in {1..5}
do
    for datasetsize in 50 100 200 400
    # for datasetsize in 50 100
    do
        for parallelism in 12 10 8 6 4 2 1
        # for parallelism in 12 6
        do
            cpusetmax=$(( parallelism - 1 ))
            cpusetmin=0
            for iterations in 1 2 5 10 20
            # for iterations in 1 5
            do
                    docker-compose -p $USER -f flink-pagerank-local-streaming.yml down -v
                    TESTED_CPU_SET="$cpusetmin-$cpusetmax" BACKFILL=0 BATCH_SIZE=100000000 ALLOW_LATENCY=1000 PARALLELISM=$parallelism PAGERANK_ITERATIONS=$iterations INPUT_FILENAME=livejournal_$datasetsize.json docker-compose -p $USER -f flink-pagerank-local-streaming.yml up > pagerank-flink-results/streaming/result-28-03-2023-$datasetsize-$parallelism-$iterations-$try.txt
                done
        done
    done
done