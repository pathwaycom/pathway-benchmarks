export STATS_SHORT=1
export STATS_TIMELINE=1
export STATS_PATHWAY_PTIME_AGGREGATED=0
export STATS_TIME_AGGREGATED=1
export CORES=1
export WORKERS=1
export ENGINE_TYPE=pathway
export BENCHMARK_TYPE=wordcount
export COMMIT_FREQUENCY=5
export AUTOCOMMIT_FREQUENCY_MS=100
export DATASET_WARMUP_PREFIX_LENGTH=1000000
export STREAMER_WAIT_TIME_MS=25000
export STREAMER_EMIT_INTERVAL_MS=8


RATE_PER_SECOND=25000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=25000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=50000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=50000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=60000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=60000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=70000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=70000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=80000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=80000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=90000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=90000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=100000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=100000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=125000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=125000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=150000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=150000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=175000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=175000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=200000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=200000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=225000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=225000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=250000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=250000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=275000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=275000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=300000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=300000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=350000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=350000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=400000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=400000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=450000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=450000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=500000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=500000 docker-compose -f docker-compose-pathway.yml down -v

export AUTOCOMMIT_FREQUENCY_MS=300

RATE_PER_SECOND=25000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=25000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=50000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=50000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=60000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=60000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=70000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=70000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=80000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=80000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=90000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=90000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=100000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=100000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=125000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=125000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=150000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=150000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=175000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=175000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=200000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=200000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=225000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=225000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=250000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=250000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=275000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=275000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=300000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=300000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=350000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=350000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=400000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=400000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=450000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=450000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=500000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=500000 docker-compose -f docker-compose-pathway.yml down -v

export AUTOCOMMIT_FREQUENCY_MS=10

RATE_PER_SECOND=25000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=25000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=50000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=50000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=60000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=60000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=70000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=70000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=80000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=80000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=90000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=90000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=100000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=100000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=125000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=125000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=150000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=150000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=175000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=175000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=200000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=200000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=225000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=225000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=250000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=250000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=275000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=275000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=300000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=300000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=350000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=350000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=400000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=400000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=450000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=450000 docker-compose -f docker-compose-pathway.yml down -v

RATE_PER_SECOND=500000 docker-compose -f docker-compose-pathway.yml run stats-collector
RATE_PER_SECOND=500000 docker-compose -f docker-compose-pathway.yml down -v

