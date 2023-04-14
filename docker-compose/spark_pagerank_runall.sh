#!/bin/bash

export REPEAT=5
export ITERATIONS="1,2,5,10,20"
export SCRIPTS="spark_pagerank_sql.py,spark_pagerank_example.py"
export DATASETS="datasets/soc-LiveJournal1.json"
export MEMORY="20g"

export CPUSET="6"
export CPUS=1
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v

export CPUSET="6-7"
export CPUS=2
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v

export CPUSET="6-9"
export CPUS=4
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v

export CPUSET="6-11"
export CPUS=6
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v

export CPUSET="4-11"
export CPUS=8
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v

export CPUSET="2-11"
export CPUS=10
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v

export CPUSET="0-11"
export CPUS=12
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v


export SCRIPTS="graphxpagerank.jar"
export DATASETS="datasets/soc-LiveJournal1.tsv"

export CPUSET="6"
export CPUS=1
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v

export CPUSET="6-7"
export CPUS=2
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v

export CPUSET="6-9"
export CPUS=4
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v

export CPUSET="6-11"
export CPUS=6
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v

export CPUSET="4-11"
export CPUS=8
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v

export CPUSET="2-11"
export CPUS=10
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v

export CPUSET="0-11"
export CPUS=12
docker-compose -f docker-compose-spark-pagerank.yml up
docker-compose -f docker-compose-spark-pagerank.yml down -v