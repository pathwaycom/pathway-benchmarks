name := "wcount"
version := "1.0"
scalaVersion := "2.12.15"


val sparkVersion = "3.3.1"

libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-core" % sparkVersion,
  "org.apache.spark" %% "spark-streaming" % sparkVersion,
  "org.apache.spark" %% "spark-sql" % sparkVersion
//   "org.apache.spark" %% "spark-streaming-twitter" % sparkVersion
)
