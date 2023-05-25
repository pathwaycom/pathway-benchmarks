FROM flink:1.16-scala_2.12


RUN apt-get update
RUN apt-get install -y openjdk-11-jdk
RUN apt-get install -y maven

WORKDIR /app

RUN wget https://downloads.lightbend.com/scala/2.12.8/scala-2.12.8.deb
RUN dpkg -i scala-2.12.8.deb

COPY pagerank /app
RUN mvn clean install -Pdocker-build 1>&2