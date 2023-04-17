#!/bin/bash

for parallelism in 1 2 4 6 8 10 12
# for parallelism in 1 2
do
    cpusetmax=$(( parallelism - 1 ))      
    for iterations in 1 2 5 10 20
    # for iterations in 1 2
    do
        for try in {1..5}
        do
            docker-compose -p $USER -f flink-pagerank-local.yml down -v
            TESTED_CPU_SET="0-$cpusetmax" PARALLELISM=$parallelism PAGERANK_ITERATIONS=$iterations INPUT_FILENAME=full.json docker-compose -p $USER -f flink-pagerank-local.yml up > result-$parallelism-$iterations-$try.txt
        done
    done
done