import argparse

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat_ws, from_json
from pyspark.sql.types import StringType, StructField, StructType

IN_BOOTSTRAP_SERVERS = "kafka:9092"
OUT_BOOTSTRAP_SERVERS = "kafka:9092"
IN_TOPIC = "test_0"
OUT_TOPIC = "test_1"

# default set to 100 ms, as it is some balance between being close to real time (0ms)
# and the fact that spark complains in logs when it gets late (which takes non zero time)

# should be overwritten on spark-submit, to achieve desired throughput / latency tradeoff
COMMIT_INTERVAL = "100 milliseconds"

parser = argparse.ArgumentParser()
parser.add_argument("--commit_interval", help="microbatch length")
args = parser.parse_args()
if args.commit_interval:
    COMMIT_INTERVAL = args.commit_interval + " milliseconds"


spark = SparkSession.builder.appName(
    "StructuredStreamingWordCountKafkaToKafka"
).getOrCreate()


# that disables all further INFO / DEBUG logs, not sure how properly disable them
# from the very beginning
spark.sparkContext.setLogLevel("WARN")
schema = StructType(
    [
        StructField("word", StringType(), True),
    ]
)

# set up input topic
df = (
    spark.readStream.format("kafka")
    .option("startingOffsets", "latest")
    .option("kafka.bootstrap.servers", IN_BOOTSTRAP_SERVERS)
    .option("subscribe", IN_TOPIC)
    .load()
)

# parse json
json = (
    df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")
    .select(from_json(col("value"), schema).alias("data"))
    .select("data.*")
)


# generate running word count
wordCounts = (
    json.groupBy("word")
    .count()
    .withColumnRenamed("count", "wcount")
    .selectExpr("word", "CAST(wcount AS STRING)")
)
output = wordCounts.select(
    concat_ws(",", wordCounts.word, wordCounts.wcount).alias("value")
)

# set up output topic
output.writeStream.outputMode("update").format("kafka").option(
    "checkpointLocation", "./chkpt"
).option("kafka.bootstrap.servers", OUT_BOOTSTRAP_SERVERS).option(
    "topic", OUT_TOPIC
).option(
    "enable.partition.eof", "false"
).trigger(
    processingTime=COMMIT_INTERVAL
).start().awaitTermination()
