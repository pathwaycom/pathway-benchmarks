FROM maven:3.8.3-openjdk-17
WORKDIR /app
COPY pom.xml pom.xml
COPY src src
RUN mvn package -Dmaven.test.skip

FROM openjdk:17
COPY --from=0 /app/target/kafka-streams-word-count.jar /app/kafka-streams-word-count.jar
ENTRYPOINT ["java", "-jar", "app/kafka-streams-word-count.jar"]
