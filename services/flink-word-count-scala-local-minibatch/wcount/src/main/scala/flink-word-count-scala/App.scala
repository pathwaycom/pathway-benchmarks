import org.apache.flink.api.common.eventtime.WatermarkStrategy
import org.apache.flink.api.common.typeinfo.Types
import org.apache.flink.api.common.serialization.SimpleStringSchema
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



import org.apache.flink.streaming.api.scala._
import org.apache.flink.api.scala.ExecutionEnvironment
// import org.apache.flink.streaming.api.environment.RemoteStreamEnvironment

object App
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

        // val config = new Configuration();
        // config.setString("taskmanager.memory.network.min", "6 Gb")
        // config.setString("taskmanager.memory.network.fraction", "1") 

        // val env = new LocalStreamEnvironment(config)
        val env = StreamExecutionEnvironment.createLocalEnvironment(1)

        // val env = StreamExecutionEnvironment.getExecutionEnvironment
        // env.setRuntimeMode(RuntimeExecutionMode.BATCH);
        env.setMaxParallelism(1)
        val tableEnv = StreamTableEnvironment.create(env)

        var configuration = tableEnv.getConfig
        configuration.set("table.exec.mini-batch.enabled", "true")
        configuration.set("table.exec.mini-batch.allow-latency", s"${pTime} ms")
        configuration.set("table.exec.mini-batch.size", "5000")
        configuration.set("table.optimizer.agg-phase-strategy", "TWO_PHASE"); 
        configuration.set("table.optimizer.incremental-agg-enabled", "true");
        
        // val env = new RemoteStreamEnvironment("flink-wordcount-taskmanager", 3456, config, "wcount-1.0-SNAPSHOT.jar")
        // val env = ExecutionEnvironment.getExecutionEnvironment()
        val names = Array("word")

        val jsonDes =  new JsonRowDeserializationSchema(Types.ROW_NAMED(names ,Types.STRING))
        // val deserializer = KafkaRecordDeserializationSchema.valueOnly(jsonDes)

        val kafkaSource = KafkaSource.builder()
        .setBootstrapServers("kafka:9092")
        .setTopics("test_0")
        .setGroupId("scala_worker_consumer")
        .setStartingOffsets(OffsetsInitializer.latest())
        .setValueOnlyDeserializer(jsonDes) 
        .build()

        val serializer = KafkaRecordSerializationSchema.builder()
        .setValueSerializationSchema(new SimpleStringSchema())
        .setTopic("test_1")
        .build()

        val kafkaSink = KafkaSink.builder()
        .setBootstrapServers("kafka:9092")
        .setRecordSerializer(serializer)
        .build()

        val stream = env.fromSource(kafkaSource, WatermarkStrategy.noWatermarks(), "Kafka Source").map(v=>v.getField(0))
        val table = tableEnv.fromDataStream(stream)

        tableEnv.createTemporaryView("words", table)
        val resultTable = tableEnv.sqlQuery("select f0, count(*) from words group by f0")
        val resultStream =  tableEnv.toChangelogStream(resultTable)
        // resultStream.print()
        val formattedResultStream = resultStream
        .map(v => s"${v.getField(0)},${v.getField(1)},${v.getKind().shortString()}")
        
        formattedResultStream.sinkTo(kafkaSink)

        env.execute("wordcount pass")
    }
}