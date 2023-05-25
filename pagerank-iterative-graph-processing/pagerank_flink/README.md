To run all the Flink pagerank benchmarks:

1. Make sure that you have all the data files, i.e.:
  - subdir `batch/pagerank/data` contains:
    * `livejournal.json` (full livejournal dataset)
    * `livejournal_truncated.json` (first 5M edges)
    * `livejournal_400.json` (first 400k edges)
  - subdir `streaming/pagerank/data` contains:
    * `livejournal_truncated.json`
    * `livejournal_400.json`

2. (Optionally) Build the containers with
  - `docker-compose -p flink_batch_$USER -f batch/docker-compose.yml build`
  - `docker-compose -p flink_streaming_$USER -f streaming/docker-compose.yml build`

3. Run `flink_pagerank_all_final.sh`.
This will run all benchmarks (can take few hours) and will produce log file for each run

4. Extract processing times and memory usage from log files for all runs by invoking `flink_pagerank_all_final_get_stats.sh`.

> If you want to extract statistics for a single run, just run `python stats_from_log.py path/to/logfile`