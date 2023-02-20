import org.apache.flink.api.common.eventtime.WatermarkStrategy
import org.apache.flink.api.common.typeinfo.Types
import org.apache.flink.api.common.serialization.SimpleStringSchema
import org.apache.flink.connector.kafka.sink.{KafkaRecordSerializationSchema, KafkaSink}
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer
import org.apache.flink.connector.kafka.source.KafkaSource
import org.apache.flink.connector.kafka.source.reader.deserializer.KafkaRecordDeserializationSchema
 
import org.apache.flink.configuration.Configuration
import org.apache.flink.formats.csv.CsvRowSerializationSchema
import org.apache.flink.formats.csv.CsvRowSerializationSchema.Builder
import org.apache.flink.api.common.typeinfo.TypeInformation
import org.apache.flink.formats.json.JsonRowDeserializationSchema
import org.apache.flink.formats.json.JsonRowDeserializationSchema.Builder



import org.apache.flink.streaming.api.scala._
import org.apache.flink.api.scala.ExecutionEnvironment
// import org.apache.flink.streaming.api.environment.RemoteStreamEnvironment


class WordWithCount(var word: String, var count: Int) {
    def this() {
      this(null, -1)
    }
}

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
        // I'm a little bit confused with how / why the line below works (due to the fact I don't know scala well)
        val env = StreamExecutionEnvironment.getExecutionEnvironment
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
        .setValueOnlyDeserializer(jsonDes) //fix me, for proper wordcount
        .build()

        val serializer = KafkaRecordSerializationSchema.builder()
        .setValueSerializationSchema(new SimpleStringSchema())
        .setTopic("test_1")
        .build()

        val kafkaSink = KafkaSink.builder()
        .setBootstrapServers("kafka:9092")
        .setRecordSerializer(serializer)
        .build()

        val lines = env.fromSource(kafkaSource, WatermarkStrategy.noWatermarks(), "Kafka Source")

        lines.map(v => (v.getField(0),1))
        .keyBy(v => v._1)
        .reduce((u,v) => (u._1, u._2+v._2))
        .map(line => s"${line._1},${line._2}")
        .sinkTo(kafkaSink)

        env.execute("wordcount pass")
    }
}