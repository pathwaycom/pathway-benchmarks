# Running Flink Pagerank benchmark

1. Copy dataset to `public/pathway-benchmarks/services/flink-pagerank/pagerank/data/`

2. Change `FLINK_UI_PORT` in `public/pathway-benchmarks/docker-compose/flink.env`

3. Navigate to `public/pathway-benchmarks/docker-compose`

4. Spin up Flink cluster:
`docker-compose --env-file flink.env -p $USER -f flink-pagerank.yml up --build`

5. Submit job to execution
`docker-compose --env-file flink.env -p $USER -f flink-pagerank.yml exec flink-pagerank-jobmanager flink run -c App /opt/flink/usrlib/pagerank-1.0-SNAPSHOT-jar-with-dependencies.jar --pagerank_iterations 5 -input filename.json`

6. View `localhost:FLINK_UI_PORT` for Flink UI to track computation and see final numbers (jobs -> completed jobs)

# Changing app code and rerunning
You can change app code without rebuilding docker

  * make your changes (it will sync instantaneously due to docker volume)
  * rebuild app
  `docker-compose --env-file variables_ext.env -p $USER -f flink-pagerank.yml exec flink-pagerank-jobmanager ./build.sh`
  * submit job to execution as in step 4
