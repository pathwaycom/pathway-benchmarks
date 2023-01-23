import argparse

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import IntegerType, StructField, StructType

IN_BOOTSTRAP_SERVERS = "kafka:9092"
OUT_BOOTSTRAP_SERVERS = "kafka:9092"
IN_TOPIC = "test_0"
OUT_TOPIC = "test_1"

# default set to 100 ms, as it is some balance between being close to real time (0ms)
# and the fact that spark complains in logs when it gets late (which takes non zero time)

# should be overwritten on spark-submit, to achieve desired throughput / latency tradeoff
COMMIT_INTERVAL = "100 milliseconds"

parser = argparse.ArgumentParser()
parser.add_argument("--commit_interval", help="amount of time between checkpoints")
args = parser.parse_args()
if args.commit_interval:
    COMMIT_INTERVAL = args.commit_interval + " milliseconds"


spark = SparkSession.builder.appName(
    "StructuredStreamingContinuousIncrement"
).getOrCreate()


# that disables all further INFO / DEBUG logs, not sure how properly disable them
# from the very beginning
spark.sparkContext.setLogLevel("WARN")

# set up input topic
df = (
    spark.readStream.format("kafka")
    .option("startingOffsets", "earliest")
    .option("kafka.bootstrap.servers", IN_BOOTSTRAP_SERVERS)
    .option("subscribe", IN_TOPIC)
    .load()
)

# parse json
schema = StructType(
    [
        StructField("number", IntegerType(), True),
    ]
)
json = (
    df.selectExpr("CAST(value AS STRING)")
    .select(from_json(col("value"), schema).alias("data"))
    .select("data.*")
)

# increment
output = json.select((json.number + 1).alias("value")).selectExpr(
    "CAST(value AS STRING)"
)

# set up output topic
output.writeStream.outputMode("append").format("kafka").option(
    "checkpointLocation", "./chkpt"
).option("kafka.bootstrap.servers", OUT_BOOTSTRAP_SERVERS).option(
    "topic", OUT_TOPIC
).option(
    "enable.partition.eof", "false"
).trigger(
    continuous=COMMIT_INTERVAL
).start().awaitTermination()
