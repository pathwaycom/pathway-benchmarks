FROM flink:1.16-scala_2.12


RUN apt-get update
RUN apt-get install -y openjdk-11-jdk
RUN apt-get install -y maven

WORKDIR /app

RUN wget https://downloads.lightbend.com/scala/2.12.8/scala-2.12.8.deb
RUN dpkg -i scala-2.12.8.deb

COPY pagerank /app
RUN mvn clean install -Pdocker-build 1>&2

# CMD java -cp /opt/flink/lib/*:/opt/flink/usrlib/pagerank-1.0-SNAPSHOT-jar-with-dependencies.jar App --pagerank_iterations 1 --input livejournal_truncated.json
# CMD tail -f /dev/null