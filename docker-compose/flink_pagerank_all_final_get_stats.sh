#!/bin/bash

# Before running this script, make sure that:
# - /services/flink-pagerank/pagerank/data contains:
#   * livejournal.json
#   * livejournal_truncated.json

# - /services/flink-pagerank-streaming/pagerank/data contains:
#   * livejournal_truncated.json
#   * livejournal_400.json

rundate="21-04-2023"
iterations=5

# batch benchmark
for dataset in "livejournal_400" "livejournal_truncated" "livejournal"
do
    for parallelism in 1 2 4 6
    do
        for try in {1..5}
        do
            res=$(python stats_from_log.py pagerank-flink-results/batch/result-$rundate-$dataset-$parallelism-$iterations-$try.txt)
            echo flink $dataset $parallelism $iterations $res mateusz/flink-pagerank-reuse cf96a9cfb35f2333e654fc77a13287d46d935d41 $rundate unlimited pathwayv5
        done
    done
done

