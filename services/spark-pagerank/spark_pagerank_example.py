import csv
import sys
import time
import uuid
from operator import add
from typing import Iterable, List, Tuple

from pyspark.resultiterable import ResultIterable
from pyspark.sql import Row, SparkSession


def computeContribs(urls: ResultIterable[str], rank: int) -> Iterable[Tuple[str, int]]:
    """Calculates URL contributions to the rank of other URLs."""
    num_urls = len(urls)
    for url in urls:
        yield (url, rank // num_urls)


def parseNeighbors(row: Row) -> Tuple[str, str]:
    """Parses a urls pair string into urls pair."""
    return row["u"], row["v"]


def save_tsv(res: List[Tuple[str, int]], filename: str) -> None:
    with open(filename, "w") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(res)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: pagerank <file> <iterations>", file=sys.stderr)
        sys.exit(-1)

    print(
        "WARN: This is a naive implementation of PageRank and is given as an example!\n"
        + "Please refer to PageRank implementation provided by graphx",
        file=sys.stderr,
    )

    # Initialize the spark context.
    spark = SparkSession.builder.appName("PythonPageRank").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # Loads in input file. It should be in format of:
    #     URL         neighbor URL
    #     URL         neighbor URL
    #     URL         neighbor URL
    #     ...
    t_start = time.time()
    lines = spark.read.json(sys.argv[1]).rdd

    # Loads all URLs from input file and initialize their neighbors.
    links = lines.map(lambda urls: parseNeighbors(urls)).distinct().groupByKey().cache()

    # Loads all URLs with other URL(s) link to from input file and initialize ranks of them to one.
    ranks = links.map(lambda url_neighbors: (url_neighbors[0], 6_000))

    base = links.map(lambda urls: (urls[0], 0)).distinct()

    # Calculates and updates URL ranks continuously using PageRank algorithm.
    for iteration in range(int(sys.argv[2])):
        # Calculates URL contributions to the rank of other URLs.
        contribs = links.join(ranks).flatMap(
            lambda url_urls_rank: computeContribs(
                url_urls_rank[1][0], url_urls_rank[1][1]  # type: ignore[arg-type]
            )
        )

        contribs = contribs.union(base)

        # Re-calculates URL ranks based on neighbor contributions.
        ranks = contribs.reduceByKey(add).mapValues(
            lambda rank: (rank * 5) // 6 + 1_000
        )

    ranks.saveAsTextFile(f"/tmp/{uuid.uuid1()}")
    # res = ranks.collect()
    t_end = time.time()
    print(t_end - t_start)
    # filename = sys.argv[1]
    # iterations = sys.argv[2]
    # save_tsv(res, f"results/example_{iterations}_{os.path.basename(filename)}")

    spark.stop()
