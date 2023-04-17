package com.pathway

import org.apache.spark.graphx.GraphLoader
import org.apache.spark.sql.SparkSession
import org.apache.spark.graphx.lib.PageRank

object GraphxPagerank {
  def main(args: Array[String]): Unit = {
    // Creates a SparkSession.
    val spark = SparkSession
      .builder
      .appName(s"${this.getClass.getSimpleName}")
      .getOrCreate()
    val sc = spark.sparkContext
    sc.setLogLevel("WARN")

    // $example on$
    // Load the edges as a graph
    val t_start = System.nanoTime()
    val graph = GraphLoader.edgeListFile(sc, args(0))
    // Run PageRank
    val ranks = PageRank.run(graph, args(1).toInt, 1.0/6.0).vertices

    val result = ranks.collect()
    val t_end = System.nanoTime()

    println((t_end-t_start).toDouble / 1e9)
    // Print the result
    // println(ranks.collect().mkString("\n"))
    // $example off$
    spark.stop()
  }
}