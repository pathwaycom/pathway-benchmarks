FROM flink:1.16.1-scala_2.12

WORKDIR /flink-word-count-scala
RUN apt-get update
RUN apt-get install -y openjdk-11-jdk
RUN apt-get install -y maven

COPY wcount wcount
RUN cd wcount && mvn clean install -Pdocker-build 1>&2
RUN cd wcount && mvn package -Pdocker-build 1>&2

CMD java -cp /opt/flink/lib/*:/opt/flink/usrlib/wcount-1.0-SNAPSHOT.jar App --commit_interval  ${AUTOCOMMIT_FREQUENCY_MS} --parallelism $CORES
