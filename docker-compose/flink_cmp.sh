ENGINE_TYPE=pathway RATE_PER_SECOND=200000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log09.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=250000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log09.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=pathway RATE_PER_SECOND=300000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-pathway.yml up stats-collector> pathway_log09.txt>&1 --build
docker-compose -p $USER down --remove-orphans


ENGINE_TYPE=flink_vanilla RATE_PER_SECOND=200000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_vanilla RATE_PER_SECOND=250000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_vanilla RATE_PER_SECOND=300000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans


ENGINE_TYPE=flink_vanilla_local RATE_PER_SECOND=200000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_vanilla_local RATE_PER_SECOND=250000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_vanilla_local RATE_PER_SECOND=300000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans


ENGINE_TYPE=flink_minibatch RATE_PER_SECOND=200000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-minibatch.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_minibatch RATE_PER_SECOND=250000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-minibatch.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_minibatch RATE_PER_SECOND=300000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-minibatch.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans


ENGINE_TYPE=flink_minibatch_local RATE_PER_SECOND=200000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-minibatch-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_minibatch_local RATE_PER_SECOND=250000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-minibatch-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans

ENGINE_TYPE=flink_minibatch_local RATE_PER_SECOND=300000 docker-compose -p $USER --env-file variables_ext.env -f docker-compose-flink-word-count-minibatch-local.yml up stats-collector> flink_log.txt>&1 --build
docker-compose -p $USER down --remove-orphans
