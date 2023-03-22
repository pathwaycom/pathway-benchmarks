import csv
import json
import sys
import time
import uuid
from operator import add
from typing import Iterable, List, Tuple

from pyspark.sql import SparkSession


def parse_row_json(row: str) -> Tuple[int, int]:
    edge = json.loads(row.strip())
    return edge["u"], edge["v"]


def propagate(entry) -> Iterable[Tuple[int, int]]:
    """
    :return: (vertex, rank_contribution)
    """
    vertex, (rank, neighbors) = entry
    yield (vertex, 0)
    if neighbors is None:
        return
    n = len(neighbors)
    for neighbor in neighbors:
        yield (neighbor, (5 * rank) // (6 * n))


def save_tsv(res: List[Tuple[int, int]], filename: str) -> None:
    with open(filename, "w") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(res)


spark = SparkSession.builder.appName("SparkPageRank").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

sc = spark.sparkContext

filename = sys.argv[1]
t_start = time.time()
edges = sc.textFile(filename).map(parse_row_json)
neighbors = edges.groupByKey()
ranks = edges.flatMap(lambda edge: edge).distinct().map(lambda vertex: (vertex, 6_000))

iterations = int(sys.argv[2]) if len(sys.argv) >= 3 else 5
for _ in range(iterations):
    contibutions = ranks.leftOuterJoin(neighbors).flatMap(propagate)
    ranks = contibutions.reduceByKey(add).mapValues(lambda rank: rank + 1_000)

ranks.saveAsTextFile(f"/tmp/{uuid.uuid1()}")
# res = ranks.collect()

t_end = time.time()
print(t_end - t_start)

# save_tsv(res, f"results/{iterations}_{os.path.basename(filename)}")

spark.stop()
