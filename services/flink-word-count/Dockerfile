FROM flink:1.16-scala_2.12

WORKDIR /flink-word-count-scala
RUN apt-get update
RUN apt-get install -y openjdk-11-jdk
RUN apt-get install -y maven

RUN wget https://downloads.lightbend.com/scala/2.12.8/scala-2.12.8.deb
RUN dpkg -i scala-2.12.8.deb

# CMD dpkg -L scala | grep jar

# CMD ls /usr/bin/scala
# CMD pyspark --version && spark-submit --version

# RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | tee /etc/apt/sources.list.d/sbt.list
# RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | tee /etc/apt/sources.list.d/sbt_old.list
# RUN curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | apt-key add
# RUN apt-get update
# RUN apt-get -y install sbt

COPY wcount wcount
RUN cd wcount && mvn clean install -Pdocker-build 1>&2
RUN cd wcount && mvn package -Pdocker-build 1>&2

# RUN cp /opt/flink/usrlib/wcount-1.0-SNAPSHOT.jar /opt/flink/lib/wcount-1.0-SNAPSHOT.jar
# CMD /opt/flink/bin/standalone-job.sh start-foreground /opt/flink/usrlib/wcount-1.0-SNAPSHOT.jar

# ENV SQL_GATEWAY_CLASSPATH /opt/flink/usrlib/wcount-1.0-SNAPSHOT-jar-wirth-dependencies.jar
# ENV INTERNAL_HADOOP_CLASSPATHS /opt/flink/usrlib/


CMD java -jar /opt/flink/usrlib/wcount-1.0-SNAPSHOT-jar-with-dependencies.jar --commit_interval  ${AUTOCOMMIT_FREQUENCY_MS} --parallelism $CORES
# CMD ls /opt/flink/usrlib/*
# CMD cat /opt/flink/bin/flink-daemon.sh
