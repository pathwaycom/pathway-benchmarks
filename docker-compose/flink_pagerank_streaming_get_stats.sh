#!/bin/bash

for datasetsize in 50 100 200 400
# for datasetsize in 50 100 200
do
    for parallelism in 12 10 8 6 4 2 1
    # for parallelism in 12 1
    do
        for iterations in 1 2 5 10 20
        # for iterations in 1 5
        do
            for try in {1..5}
            do
                res=$(python stats_from_log.py pagerank-flink-results/streaming/result-28-03-2023-$datasetsize-$parallelism-$iterations-$try.txt)
                echo "flink-streaming-minibatch livejournal-$datasetsize" $parallelism $iterations $res mateusz/branch commit 2023-03-22 1000 pathwayv5
            done
        done
    done
done