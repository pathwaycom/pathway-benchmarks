FROM python:3.10

RUN apt-get update
RUN apt-get install -y openjdk-11-jdk

WORKDIR /spark-word-count

COPY ./requirements.txt /spark-word-count/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /spark-word-count/requirements.txt

COPY ./structured_streaming_wordcount_kafka.py /spark-word-count/structured_streaming_wordcount_kafka.py
CMD ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.1", "structured_streaming_wordcount_kafka.py", "1>&2"]
