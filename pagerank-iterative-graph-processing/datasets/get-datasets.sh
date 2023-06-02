wget https://snap.stanford.edu/data/soc-LiveJournal1.txt.gz
gzip -d soc-LiveJournal1.txt.gz

python pagerank-backfilling-gen.py --output-path pagerank-full.jsonlines --total-lines 1000000000 --backfilling-start 1000000000 --backfilling-step 1
python pagerank-backfilling-gen.py --output-path pagerank-full-one.jsonlines --total-lines 1000000000 --backfilling-start 68993772 --backfilling-step 1
python pagerank-backfilling-gen.py --output-path pagerank-5m-batch.jsonlines --total-lines 5000000 --backfilling-start 1000000000 --backfilling-step 1
python pagerank-backfilling-gen.py --output-path pagerank-5m-streaming.jsonlines --total-lines 5000000 --backfilling-start 1000 --backfilling-step 1000
python pagerank-backfilling-gen.py --output-path pagerank-5m-backfilling.jsonlines --total-lines 5000000 --backfilling-start 4500000 --backfilling-step 1000
python pagerank-backfilling-gen.py --output-path pagerank-400k-batch.jsonlines --total-lines 400000 --backfilling-start 1000000000 --backfilling-step 1
python pagerank-backfilling-gen.py --output-path pagerank-400k-streaming.jsonlines --total-lines 400000 --backfilling-start 1000 --backfilling-step 1000

# copy and generate data for flink (which does not use COMMIT messages)
# batch
cp pagerank-full.jsonlines ../pagerank_flink/batch/pagerank/data/livejournal.json
cat ../pagerank_flink/batch/pagerank/data/livejournal.json | head -n 5000000 > ../pagerank_flink/batch/pagerank/data/livejournal_truncated.json
cat ../pagerank_flink/batch/pagerank/data/livejournal.json | head -n 400000 > ../pagerank_flink/batch/pagerank/data/livejournal_400.json
# streaming
cp ../pagerank_flink/batch/pagerank/data/livejournal_truncated.json ../pagerank_flink/streaming/pagerank/data/livejournal_truncated.json
cp ../pagerank_flink/batch/pagerank/data/livejournal_400.json ../pagerank_flink/streaming/pagerank/data/livejournal_400.json
