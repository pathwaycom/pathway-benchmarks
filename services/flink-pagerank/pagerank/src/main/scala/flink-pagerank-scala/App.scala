/**
 * Pagerank in Flink.
 * Reimplementation of Pathway's /public/pathway/python/pathway/stdlib/graphs/pagerank/
 * (loop unrolling)
 */

import org.apache.flink.api.common.eventtime.WatermarkStrategy
import org.apache.flink.api.common.typeinfo.Types
import org.apache.flink.api.common.serialization.SimpleStringSchema
import org.apache.flink.table.api.{EnvironmentSettings, TableEnvironment}
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
import org.apache.flink.api.common.RuntimeExecutionMode
import org.apache.flink.api.java.utils.ParameterTool
import org.apache.flink.table.api.bridge.scala.StreamTableEnvironment
import org.apache.flink.metrics.slf4j.Slf4jReporterFactory

object App
{
    def main(args: Array[String])
    {
        val parameters = ParameterTool.fromArgs(args)
        val pagerank_iterations: Int = parameters.getRequired("pagerank_iterations").toInt
        val inputFileName = parameters.getRequired("input")
        val parallelism = parameters.getRequired("parallelism")

        val configuration = new Configuration;
        configuration.setString("table.exec.resource.default-parallelism", s"${parallelism}")
        configuration.setString("taskmanager.memory.managed.size", "10G")

        configuration.setString("metrics.reporter.slf4j.factory.class", "org.apache.flink.metrics.slf4j.Slf4jReporterFactory")
        configuration.setString("metrics.reporter.slf4j.interval", "5 SECONDS")

        val env = StreamExecutionEnvironment.createLocalEnvironment(1, configuration)

        // val tableEnv = TableEnvironment.create(settings)
        val tableEnv = StreamTableEnvironment.create(env, EnvironmentSettings.inBatchMode)
        
        tableEnv.createTemporaryTable("SourceTable", TableDescriptor.forConnector("filesystem")
        .schema(Schema.newBuilder()
            .column("u", DataTypes.INT())
            .column("v", DataTypes.INT())
            .build())
        .format("json")
        .option("path", s"file:////app/data/${inputFileName}")
        .build())

        // // Create a sink table (using SQL DDL)
        tableEnv.executeSql("CREATE TEMPORARY TABLE SinkTable (`id_rank` INT, `rank` BIGINT) WITH ('connector' = 'blackhole');")
        // tableEnv.executeSql("CREATE TEMPORARY TABLE SinkTable (`id_rank` INT, `rank` BIGINT) WITH ('connector' = 'filesystem', 'path'='file:////app/data/out.json', 'format'='json');")
        // tableEnv.executeSql("CREATE TEMPORARY TABLE SinkTable (`id_rank` INT, `rank` BIGINT) WITH ('connector' = 'print');")

        val edges = tableEnv.from("SourceTable")
        val in_vertices = edges.groupBy($"v").select($"v".as("id"), 0.as("degree0"))
        val out_vertices = edges.groupBy($"u").select($"u".as("id"), $"v".count.as("degree"))
        val degrees = in_vertices.fullOuterJoin(out_vertices.select($"id".as("id_out"), $"degree"), $"id" === $"id_out").select($"id".ifNull($"id_out").as("id"), $"degree".ifNull(0).as("degree"))
        val base = out_vertices.select($"id").minus(in_vertices.select($"id")).select($"id", 0.as("flow"))  // minus works only in batch! Reimplementing below with join+filter
        // val base = out_vertices.select($"id").leftOuterJoin(in_vertices.select($"id".as("id_in")), $"id" === $"id_in").filter($"id_in".isNull).select($"id", 0.as("flow"))
        var ranks = degrees.select($"id".as("id_rank"), 6000.as("rank"))
        
        for (_ <- 1 to pagerank_iterations) {
            var outflow = ranks.join(degrees, $"id" === $"id_rank").select($"id", ($"degree" === 0).?(0, (($"rank" * 5) / ($"degree" * 6)).floor()).as("flow"))
            var edges_flow = edges.join(outflow, $"u" === $"id").select($"v", $"flow")
            var inflows = edges_flow.groupBy($"v").select($"v".as("id"), $"flow".sum.as("flow"))
            inflows = inflows.unionAll(base)
            ranks = inflows.select($"id".as("id_rank"), ($"flow"+1000).as("rank"))
        }

        val tableResult = ranks.insertInto("SinkTable").execute()
    }

}
