package com.pathway

import org.apache.spark.sql.SparkSession
import org.apache.spark.sql.functions._

object SqlPagerank {
  def main(args: Array[String]): Unit = {
    // Creates a SparkSession.
    val spark = SparkSession
      .builder
      .appName(s"${this.getClass.getSimpleName}")
      .getOrCreate()
    import spark.sqlContext.implicits._
    val sc = spark.sparkContext
    sc.setLogLevel("WARN")

    // $example on$
    // Load the edges as a graph
    val t_start = System.nanoTime()
    
    val edges = spark.read.json(args(0)).cache()

    val in_vertices = edges
      .select($"v")
      .distinct()
      .withColumn("degree", lit(0))
      .withColumnRenamed("v", "u")
    
    val out_vertices = edges
      .groupBy($"u")
      .count()
      .withColumnRenamed("count", "degree")
    
    val degrees = in_vertices
    .union(out_vertices)
    .groupBy($"u")
    .sum("degree")
    .withColumnRenamed("sum(degree)", "degree")

    val base = out_vertices
    .select($"u")
    .except(in_vertices.select($"u"))
    .withColumn("degree", lit(0))

    var ranks = degrees.withColumn("rank", lit(6000)).drop("degree")

    val iterations = args(1).toInt

    for (_ <- 0 until iterations) {
      val outflow = degrees.join(ranks, "u")
        .withColumn("outflow", when(col("degree") > 0,
            ((col("rank") * 5) / (col("degree") * 6)).cast("int"))
        .otherwise(0))

      val edge_flows = edges.join(outflow, "u")

      val inflows = edge_flows.select($"v", $"outflow")
        .withColumnRenamed("v", "u")
        .groupBy($"u")
        .sum("outflow")

      ranks = inflows
        .union(base)
        .withColumn("rank", col("sum(outflow)") + 1000)
        .select($"u", $"rank")
    }

    val res = ranks.collect()
    val t_end = System.nanoTime()

    println((t_end-t_start).toDouble / 1e9)
    // Print the result
    // println(ranks.collect().mkString("\n"))
    // $example off$
    spark.stop()
  }
}