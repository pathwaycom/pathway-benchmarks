"""
Pathway pagerank implementation equivalent in Spark SQL.
"""

import csv
import sys
import time
import uuid
from typing import List

import pyspark.sql.functions as sf
from pyspark.sql import DataFrame, Row, SparkSession


def save_tsv(res: List[Row], filename: str) -> None:
    with open(filename, "w") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows([(row.asDict()["u"], row.asDict()["rank"]) for row in res])


spark = SparkSession.builder.appName("SparkPageRank").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

sc = spark.sparkContext

filename = sys.argv[1]
t_start = time.time()

edges = spark.read.json(filename).cache()

in_vertices = (
    edges.select(edges["v"])
    .distinct()
    .withColumn("degree", sf.lit(0))
    .withColumnRenamed("v", "u")
)
out_vertices: DataFrame = (
    edges.groupBy(sf.col("u")).count().withColumnRenamed("count", "degree")
)
degrees: DataFrame = (
    in_vertices.union(out_vertices)
    .groupBy("u")
    .sum("degree")
    .withColumnRenamed("sum(degree)", "degree")
)
base = (
    out_vertices.select("u")
    .subtract(in_vertices.select("u"))
    .withColumn("degree", sf.lit(0))
)

ranks = degrees.withColumn("rank", sf.lit(6_000)).drop("degree")

iterations = int(sys.argv[2]) if len(sys.argv) >= 3 else 5
for _ in range(iterations):
    outflow = degrees.join(ranks, "u").withColumn(
        "outflow",
        sf.when(
            sf.col("degree") > 0,
            ((sf.col("rank") * 5) / (sf.col("degree") * 6)).cast("int"),
        ).otherwise(0),
    )

    edge_flows = edges.join(outflow, "u")

    inflows = (
        edge_flows.select("v", "outflow")
        .withColumnRenamed("v", "u")
        .groupBy("u")
        .sum("outflow")
    )

    inflows = inflows.union(base)

    ranks = inflows.withColumn("rank", sf.col("sum(outflow)") + 1_000).select(
        "u", "rank"
    )

ranks.write.format("csv").save(f"/tmp/{uuid.uuid1()}")

t_end = time.time()
print(t_end - t_start)

spark.stop()
