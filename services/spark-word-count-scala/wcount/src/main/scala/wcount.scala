import org.apache.spark.sql.streaming.Trigger
import org.apache.spark.rdd.RDD
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.sql.functions._
import org.apache.spark.sql.types._

object wcount
{

    
    def main(args: Array[String])
    {
        def nextArg(map: Map[String, Any], list: List[String]): Map[String, Any] = {
            list match {
            case Nil => map
            case "--commit_interval" :: value :: tail =>
                nextArg(map ++ Map("commit_interval" -> value.toInt), tail)
            case string :: Nil =>
                nextArg(map ++ Map("filename" -> string), list.tail)
            case unknown :: _ =>
                throw new Exception("Unknown option " + unknown)
                
            }
        }

    
        val options = nextArg(Map(), args.toList)
        val pTime = options("commit_interval")

        val spark = SparkSession.builder().appName("scalaWordCount").getOrCreate()
        spark.sparkContext.setLogLevel("WARN")
        val stream = spark.readStream.format("kafka")
            .option("kafka.bootstrap.servers", "kafka:9092")
            .option("subscribe", "test_0")
            .option("startingOffsets", "latest")
            .load()
        
        val json = stream.selectExpr("cast (value as String) as data")

        val schema = new StructType()
        .add("word", StringType, true)
    
        val parsed = json.withColumn("jsonData",from_json(col("data"),schema)).select("jsonData.*")

        val res = parsed.groupBy("word").count()
        val output = res.select(concat(res("word"),lit(","),res("count")).alias("value"))
        
        output.writeStream
        .outputMode("update")
        .option("checkpointLocation", "./chkpt")
        .format("kafka")
        .option("kafka.bootstrap.servers", "kafka:9092")
        .option("topic", "test_1")
        .trigger(Trigger.ProcessingTime(s"$pTime milliseconds"))        
        .start()
        .awaitTermination()

    }
}