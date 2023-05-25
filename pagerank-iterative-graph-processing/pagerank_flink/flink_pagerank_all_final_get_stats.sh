#!/bin/bash

# Before running this script, make sure that:
# - /services/flink-pagerank/pagerank/data contains:
#   * livejournal.json
#   * livejournal_truncated.json

# - /services/flink-pagerank-streaming/pagerank/data contains:
#   * livejournal_truncated.json
#   * livejournal_400.json

rundate="2023-04-22"
iterations=5

# batch benchmark
for dataset in "livejournal_400" "livejournal_truncated" "livejournal"
do
    for parallelism in 1 2 4 6
    do
        for try in {1..5}
        do
            res=$(python stats_from_log.py batch/results/result-$rundate-$dataset-$parallelism-$iterations-$try.txt)
            echo flink-batch $dataset $parallelism $iterations $res develop cf96a9cfb35f2333e654fc77a13287d46d935d41 $rundate unlimited
        done
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
        for try in {1..5}
        do                                                             
            res=$(python stats_from_log.py streaming/results/result-nobackfill-$rundate-$dataset-$parallelism-$iterations-$try.txt)
            echo flink-streaming $dataset $parallelism $iterations $res develop cf96a9cfb35f2333e654fc77a13287d46d935d41 $rundate scenarioA
        done
    done
done

# B) backfill 4.5M
backfill=4500000
for dataset in "livejournal_truncated"
do
    for parallelism in 1 2 4 6
    do
        for try in {1..5}
        do                                                             
            res=$(python stats_from_log.py streaming/results/result-backfill-4.5M-$rundate-$dataset-$parallelism-$iterations-$try.txt)
            echo flink-streaming $dataset $parallelism $iterations $res develop cf96a9cfb35f2333e654fc77a13287d46d935d41 $rundate scenarioB
        done
    done
done

# C) backfill 4999999
backfill=4999999
for dataset in "livejournal_truncated"
do
    for parallelism in 1 2 4 6
    do
        for try in {1..5}
        do                                                             
            res=$(python stats_from_log.py streaming/results/result-backfill-4999999-$rundate-$dataset-$parallelism-$iterations-$try.txt)
            echo flink-streaming $dataset $parallelism $iterations $res develop cf96a9cfb35f2333e654fc77a13287d46d935d41 $rundate scenarioC
        done
    done
done