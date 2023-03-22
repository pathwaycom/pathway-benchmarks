#!/bin/bash

export REPEAT=3
export ITERATIONS="1,2,5,10,20"
export SCRIPTS="spark_pagerank_4.py,spark_pagerank_2.py,spark_pagerank_sql.py,spark_pagerank_example.py,sqlpagerank.jar"
export DATASETS="datasets/livejournal_truncated.json"
export CPUSET="6"
export CPUS=1
export MEMORY="4g"
docker-compose -f docker-compose-spark-pagerank.yml up -d
docker-compose -f docker-compose-spark-pagerank.yml down -v

export REPEAT=3
export ITERATIONS="5"
export SCRIPTS="spark_pagerank_4.py,spark_pagerank_2.py,spark_pagerank_sql.py,spark_pagerank_example.py,sqlpagerank.jar"
export DATASETS="datasets/livejournal_truncated_1M.json,datasets/livejournal_truncated_2M.json,datasets/livejournal_truncated_3M.json,datasets/livejournal_truncated_4M.json"
export CPUSET="6"
export CPUS=1
export MEMORY="4g"
docker-compose -f docker-compose-spark-pagerank.yml up -d
docker-compose -f docker-compose-spark-pagerank.yml down -v

export REPEAT=3
export ITERATIONS="5"
export SCRIPTS="spark_pagerank_sql.py,sqlpagerank.jar"
export DATASETS="datasets/soc-LiveJournal1.json"
export CPUSET="6"
export CPUS=1
export MEMORY="16g"
docker-compose -f docker-compose-spark-pagerank.yml up -d
docker-compose -f docker-compose-spark-pagerank.yml down -v

export REPEAT=3
export ITERATIONS="5"
export SCRIPTS="graphxpagerank.jar"
export DATASETS="datasets/soc-LiveJournal1.tsv"
export CPUSET="6"
export CPUS=1
export MEMORY="16g"
docker-compose -f docker-compose-spark-pagerank.yml up -d
docker-compose -f docker-compose-spark-pagerank.yml down -v


