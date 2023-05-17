import org.apache.flink.api.common.eventtime.WatermarkStrategy
import org.apache.flink.api.common.typeinfo.Types
import org.apache.flink.api.common.serialization.SimpleStringSchema
import org.apache.flink.streaming.connectors.kafka.table.KafkaConnectorOptions
import org.apache.flink.connector.kafka.sink.{KafkaRecordSerializationSchema, KafkaSink}
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer
import org.apache.flink.connector.kafka.source.KafkaSource
import org.apache.flink.connector.kafka.source.reader.deserializer.KafkaRecordDeserializationSchema
import org.apache.flink.table.api.bridge.scala.StreamTableEnvironment 
import org.apache.flink.table.sinks.RetractStreamTableSink

import org.apache.flink.configuration.Configuration
import org.apache.flink.formats.csv.CsvRowSerializationSchema
import org.apache.flink.formats.csv.CsvRowSerializationSchema.Builder
import org.apache.flink.api.common.typeinfo.TypeInformation
import org.apache.flink.formats.json.JsonRowDeserializationSchema
import org.apache.flink.formats.json.JsonRowDeserializationSchema.Builder
import org.apache.flink.table.api._
import org.apache.flink.streaming.api.scala._

import org.apache.flink.api.scala.ExecutionEnvironment

object App
{

    def main(args: Array[String])
    {
        def nextArg(map: Map[String, Any], list: List[String]): Map[String, Any] = {
            list match {
            case Nil => map
            case "--commit_interval" :: value :: tail =>
                nextArg(map ++ Map("commit_interval" -> value.toInt), tail)
            case "--parallelism" :: value :: tail =>
                nextArg(map ++ Map("parallelism" -> value.toInt), tail)    
            case string :: Nil =>
                nextArg(map ++ Map("filename" -> string), list.tail)
            case unknown :: _ =>
                throw new Exception("Unknown option " + unknown)
                
            }
        }

        val options = nextArg(Map(), args.toList)
        val pTime = options("commit_interval")
        val parallelism = options("parallelism")

        val configuration = new Configuration;
        configuration.setString("table.exec.resource.default-parallelism", s"${parallelism}")
        configuration.setString("table.exec.mini-batch.enabled", "true")
        configuration.setString("table.exec.mini-batch.allow-latency", s"${pTime} ms")
        configuration.setString("table.exec.mini-batch.size", "20000")
        configuration.setString("table.optimizer.agg-phase-strategy", "TWO_PHASE"); 
        configuration.setString("table.optimizer.incremental-agg-enabled", "true");
        configuration.setString("pipeline-object-reuse","true");
        
        val settings = EnvironmentSettings.newInstance
        .inStreamingMode.withConfiguration(configuration).build

        val tableEnv = TableEnvironment.create(settings)
        val table = tableEnv.createTemporaryTable("words", TableDescriptor.forConnector("kafka")
            .schema(
                Schema.newBuilder()
                .column("word", DataTypes.STRING().notNull())
                .build()
            )
            .partitionedBy("word")
            .option("topic", "test_0")
            .option("scan.startup.mode", "latest-offset")
            .option("properties.group.id", "flink_scala_wordcount_consumers")
            .option("properties.bootstrap.servers", "kafka:9092")
            .format("json")
            .build()
        )        

        val sinkTable = tableEnv.createTemporaryTable("sink", TableDescriptor.forConnector("upsert-kafka")
            .schema(
                Schema.newBuilder()
                .column("word", DataTypes.STRING().notNull())
                .column("count", DataTypes.BIGINT().notNull())
                .primaryKey("word")
                .build()
            )
            
            .option("topic", "test_1")
            .option("properties.bootstrap.servers", "kafka:9092")
            .option("key.format", "csv")
            .option("value.format", "csv")
            .build()
        )

        tableEnv.sqlQuery("select word, count(*) from words group by word").insertInto("sink").execute()

    }
}