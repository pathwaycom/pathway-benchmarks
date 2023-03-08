FROM python:3.10

WORKDIR /opt/spark

#java setup
RUN apt-get update
RUN apt-get install -y openjdk-11-jdk

# spark setup - env variables
# verify https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/ to see which hadoop versions are available
ENV SPARK_VERSION=3.3.2 \
HADOOP_VERSION=3 \
SPARK_HOME=/opt/spark 

# get spark
RUN wget --no-verbose -O apache-spark.tgz "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" \
&& mkdir -p $SPARK_HOME \
&& tar -xf apache-spark.tgz -C $SPARK_HOME --strip-components=1 \
&& rm apache-spark.tgz

# spark ports / log-directories
ENV SPARK_MASTER_PORT=7077 \
SPARK_MASTER_WEBUI_PORT=8080 \
SPARK_LOG_DIR=$SPARK_HOME/logs \
SPARK_MASTER_LOG=$SPARK_HOME/logs/spark-master.out \
SPARK_WORKER_LOG=$SPARK_HOME/logs/spark-worker.out \
SPARK_WORKER_WEBUI_PORT=8080 \
SPARK_WORKER_PORT=7000 \
SPARK_MASTER="spark://spark-master:7077" \
SPARK_WORKLOAD="master"

#web-ui, master
EXPOSE 8080 7077

RUN mkdir -p $SPARK_LOG_DIR && \
touch $SPARK_MASTER_LOG && \
touch $SPARK_WORKER_LOG && \
ln -sf /dev/stdout $SPARK_MASTER_LOG && \
ln -sf /dev/stdout $SPARK_WORKER_LOG

COPY start-spark.sh /

CMD ["/bin/bash", "/start-spark.sh"]
