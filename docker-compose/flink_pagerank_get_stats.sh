#!/bin/bash

for parallelism in 1 2 4 6 8 10 12
do
    for iterations in 1 2 5 10 20
    do
        for try in {1..5}
        do  
            res=$(python stats_from_log.py result-$parallelism-$iterations-$try.txt)
            echo "livejournal" $parallelism $iterations $res mateusz/flink-local-runall 61ae6f4f663fa9b06d680d771361e39eef73b8d7 2023-03-17 unlimited pathwayv5
            # echo "flink, livejournal, 1, $iterations, $(calc $duration/1000), $(calc $peak_memory/1024), develop" >> flink_pagerank_results.txt
        done
    done
done