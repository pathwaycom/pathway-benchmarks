ENGINE_TYPE=flink_local RATE_PER_SECOND=150000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_local RATE_PER_SECOND=175000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_local RATE_PER_SECOND=200000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_local RATE_PER_SECOND=225000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_local RATE_PER_SECOND=250000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_local RATE_PER_SECOND=275000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_local RATE_PER_SECOND=300000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_local RATE_PER_SECOND=325000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_local RATE_PER_SECOND=350000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans


ENGINE_TYPE=flink_mb_local RATE_PER_SECOND=75000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local-minibatch.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_mb_local RATE_PER_SECOND=100000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local-minibatch.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_mb_local RATE_PER_SECOND=125000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local-minibatch.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_mb_local RATE_PER_SECOND=150000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local-minibatch.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_mb_local RATE_PER_SECOND=75000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local-minibatch.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_mb_local RATE_PER_SECOND=100000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local-minibatch.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_mb_local RATE_PER_SECOND=125000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local-minibatch.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_mb_local RATE_PER_SECOND=150000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local-minibatch.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans


ENGINE_TYPE=pathway RATE_PER_SECOND=200000 AUTOCOMMIT_FREQUENCY_MS=5 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=250000 AUTOCOMMIT_FREQUENCY_MS=5 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=300000 AUTOCOMMIT_FREQUENCY_MS=5 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=350000 AUTOCOMMIT_FREQUENCY_MS=5 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=400000 AUTOCOMMIT_FREQUENCY_MS=5 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=450000 AUTOCOMMIT_FREQUENCY_MS=5 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=500000 AUTOCOMMIT_FREQUENCY_MS=5 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=550000 AUTOCOMMIT_FREQUENCY_MS=5 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=600000 AUTOCOMMIT_FREQUENCY_MS=5 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=650000 AUTOCOMMIT_FREQUENCY_MS=5 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=700000 AUTOCOMMIT_FREQUENCY_MS=5 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=750000 AUTOCOMMIT_FREQUENCY_MS=5 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans


ENGINE_TYPE=pathway RATE_PER_SECOND=200000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=250000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=300000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=350000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=400000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=450000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=500000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=550000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=600000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=650000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=700000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=750000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=200000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=250000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=300000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=350000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=400000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=450000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=500000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=550000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=600000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=650000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=700000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=750000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans


ENGINE_TYPE=kstreams RATE_PER_SECOND=75000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=100000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=125000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=150000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=175000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=200000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=225000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=250000 AUTOCOMMIT_FREQUENCY_MS=10 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=75000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=100000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=125000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=150000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=175000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=200000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=225000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=kstreams RATE_PER_SECOND=250000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-kafka-streams.yml up stats-collector> kstreams_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans


ENGINE_TYPE=spark_local RATE_PER_SECOND=75000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=100000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=125000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=150000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=175000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=200000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=225000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=250000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=275000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=300000 AUTOCOMMIT_FREQUENCY_MS=20 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=75000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=100000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=125000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=150000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=175000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=200000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=225000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=250000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=275000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=spark_local RATE_PER_SECOND=300000 AUTOCOMMIT_FREQUENCY_MS=50 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-spark-word-count-scala-local.yml up stats-collector> spark_log_cluster.txt>&1 --build
docker-compose -p $USER down --remove-orphans












