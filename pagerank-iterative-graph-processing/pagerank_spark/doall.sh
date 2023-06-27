#!/bin/bash

export REPEAT=5
export ITERATIONS="1,2,5,10,20"
export SCRIPTS="spark_pagerank_sql.py,spark_pagerank_example.py"
export DATASETS="data/pagerank-full.jsonlines"
export MEMORY="20g"

export CPUSET="6"
export CPUS=1
docker-compose up
docker-compose down -v

export CPUSET="6-7"
export CPUS=2
docker-compose up
docker-compose down -v

export CPUSET="6-9"
export CPUS=4
docker-compose up
docker-compose down -v

export CPUSET="6-11"
export CPUS=6
docker-compose up
docker-compose down -v

export CPUSET="4-11"
export CPUS=8
docker-compose up
docker-compose down -v

export CPUSET="2-11"
export CPUS=10
docker-compose up
docker-compose down -v

export CPUSET="0-11"
export CPUS=12
docker-compose up
docker-compose down -v


export SCRIPTS="graphxpagerank.jar"
export DATASETS="data/soc-LiveJournal1.txt"

export CPUSET="6"
export CPUS=1
docker-compose up
docker-compose down -v

export CPUSET="6-7"
export CPUS=2
docker-compose up
docker-compose down -v

export CPUSET="6-9"
export CPUS=4
docker-compose up
docker-compose down -v

export CPUSET="6-11"
export CPUS=6
docker-compose up
docker-compose down -v

export CPUSET="4-11"
export CPUS=8
docker-compose up
docker-compose down -v

export CPUSET="2-11"
export CPUS=10
docker-compose up
docker-compose down -v

export CPUSET="0-11"
export CPUS=12
docker-compose up
docker-compose down -v