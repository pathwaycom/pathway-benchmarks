FROM python:3.10

WORKDIR /spark-word-count-scala
RUN pip install --no-cache-dir --upgrade pyspark==3.3.1
RUN pip install --no-cache-dir --upgrade spark-submit==1.2.1
RUN apt-get update
RUN apt-get install -y openjdk-11-jdk


RUN wget https://downloads.lightbend.com/scala/2.12.15/scala-2.12.15.deb
RUN dpkg -i scala-2.12.15.deb

# CMD scala -version
# CMD pyspark --version && spark-submit --version

RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | tee /etc/apt/sources.list.d/sbt.list
RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | tee /etc/apt/sources.list.d/sbt_old.list
RUN curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | apt-key add
RUN apt-get update
RUN apt-get -y install sbt

COPY wcount wcount
RUN  cd wcount && sbt package 1>&2
# CMD ls wcount 
# CMD spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.1 wcount/target/scala-2.12/wcount_2.12-1.0.jar 1>&2
CMD spark-submit --master local[$CORES] --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.1 --driver-memory 16G --executor-memory 16G --conf spark.sql.shuffle.partitions=$(($CORES*$WORKERS)) --conf spark.streaming.kafka.maxRatePerPartition=0 --conf spark.driver.maxResultSize=16G wcount/target/scala-2.12/wcount_2.12-1.0.jar --commit_interval $AUTOCOMMIT_FREQUENCY_MS 1>&2