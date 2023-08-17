"""
Pathway pagerank implementation equivalent in Spark RDD.
"""

import csv
import json
import sys
import time
import uuid
from operator import add
from typing import List, Tuple

from pyspark.sql import SparkSession


def parse_row_json(row: str) -> Tuple[int, int]:
    edge = json.loads(row.strip())
    return edge["u"], edge["v"]


def save_tsv(res: List[Tuple[int, int]], filename: str) -> None:
    with open(filename, "w") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(res)


spark = SparkSession.builder.appName("SparkPageRank").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

sc = spark.sparkContext

filename = sys.argv[1]

t_start = time.time()
edges = sc.textFile(filename).map(parse_row_json).cache()
in_vertices = edges.map(lambda edge: edge[1]).distinct().map(lambda u: (u, 0))
out_vertices = edges.map(lambda edge: (edge[0], 1)).reduceByKey(add)
degrees = in_vertices.union(out_vertices).reduceByKey(add)
base = (
    out_vertices.leftOuterJoin(in_vertices)
    .filter(lambda entry: entry[1][1] is None)
    .map(lambda entry: (entry[0], 0))
)

ranks = degrees.map(lambda entry: (entry[0], 6_000))

iterations = int(sys.argv[2]) if len(sys.argv) >= 3 else 5
for _ in range(iterations):
    outflow = degrees.join(ranks).map(
        lambda entry: (
            entry[0],
            0 if entry[1][0] == 0 else (entry[1][1] * 5) // (entry[1][0] * 6),
        )
    )

    edges_flows = edges.join(outflow)

    inflows = edges_flows.map(lambda entry: entry[1]).reduceByKey(add)

    inflows = inflows.union(base)

    ranks = inflows.mapValues(lambda rank: rank + 1_000)

ranks.saveAsTextFile(f"/tmp/{uuid.uuid1()}")

t_end = time.time()
print(t_end - t_start)

spark.stop()
