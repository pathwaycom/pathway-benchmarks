# an example of a command that runs spark increment benchmark, 
# most likely COMMIT_FREQUENCY shuould not be specified for time oblivous benchmarks
ENGINE_TYPE=spark BENCHMARK_TYPE=increment COMMIT_FREQUENCY=5 RATE_PER_SECOND=25000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose --env-file variables.env -f docker-compose-spark-increment.yml up stats-collector --scale spark-worker=2  1>log_run.txt 2>&1
