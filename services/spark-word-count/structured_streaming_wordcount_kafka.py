import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat_ws, from_json
from pyspark.sql.types import StringType, StructField, StructType

IN_BOOTSTRAP_SERVERS = "kafka:9092"
OUT_BOOTSTRAP_SERVERS = "kafka:9092"
IN_TOPIC = "test_0"
OUT_TOPIC = "test_1"


print("spark-submit happened", file=sys.stderr)
spark = SparkSession.builder.appName("StructuredStreamingWordCountCSV").getOrCreate()


# that disables all further INFO / DEBUG logs, not sure how properly disable them
# from the very beginning
spark.sparkContext.setLogLevel("WARN")

schema = StructType(
    [
        StructField("word", StringType(), True),
    ]
)


df = (
    spark.readStream.format("kafka")
    .option("startingOffsets", "earliest")
    .option("kafka.bootstrap.servers", IN_BOOTSTRAP_SERVERS)
    .option("subscribe", IN_TOPIC)
    .load()
)
# df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")

# Parse json, split the lines into words
# the part: select("data.*") is stupid, no clue why we need to do it this way
json = (
    df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")
    .select(from_json(col("value"), schema).alias("data"))
    .select("data.*")
)


# Generate running word count
wordCounts = (
    json.groupBy("word")
    .count()
    .withColumnRenamed("count", "wcount")
    .selectExpr("word", "CAST(wcount AS STRING)")
)
output = wordCounts.select(
    concat_ws(",", wordCounts.word, wordCounts.wcount).alias("value")
)


output.writeStream.outputMode("update").format("kafka").option(
    "checkpointLocation", "./chkpt"
).option("kafka.bootstrap.servers", OUT_BOOTSTRAP_SERVERS).option(
    "topic", OUT_TOPIC
).option(
    "enable.partition.eof", "false"
).trigger(
    processingTime="100 milliseconds"
).start().awaitTermination()
