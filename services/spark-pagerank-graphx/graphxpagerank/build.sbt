import Dependencies._

ThisBuild / scalaVersion     := "2.12.15"
ThisBuild / version          := "0.1.0-SNAPSHOT"
ThisBuild / organization     := "com.pathway"
ThisBuild / organizationName := "pathway"

lazy val root = (project in file("."))
  .settings(
    name := "GraphxPagerank",
    
    libraryDependencies += "org.apache.spark" %% "spark-sql" % "3.3.1",

    // https://mvnrepository.com/artifact/org.apache.spark/spark-graphx
    libraryDependencies += "org.apache.spark" %% "spark-graphx" % "3.3.1",

  )

// See https://www.scala-sbt.org/1.x/docs/Using-Sonatype.html for instructions on how to publish to Sonatype.
