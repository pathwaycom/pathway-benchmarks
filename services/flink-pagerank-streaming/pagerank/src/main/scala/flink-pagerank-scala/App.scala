/**
 * Pagerank in Flink.
 * Reimplementation of Pathway's /public/pathway/python/pathway/stdlib/graphs/pagerank/
 * (loop unrolling)
 */

import org.apache.flink.api.common.eventtime.{Watermark, WatermarkStrategy, WatermarkGenerator, WatermarkOutput, WatermarkGeneratorSupplier, TimestampAssigner, TimestampAssignerSupplier}
import org.apache.flink.api.common.typeinfo.Types
import org.apache.flink.api.common.serialization.SimpleStringSchema
import org.apache.flink.table.api.{EnvironmentSettings, TableEnvironment}
import org.apache.flink.table.sinks.RetractStreamTableSink
import org.apache.flink.configuration.Configuration
import org.apache.flink.formats.csv.CsvReaderFormat
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
import org.apache.flink.connector.file.src.FileSource
import org.apache.flink.shaded.jackson2.com.fasterxml.jackson.annotation.JsonPropertyOrder;
import org.apache.flink.connector.file.src.reader.TextLineInputFormat
import org.apache.flink.core.fs.Path
import java.time.Duration
import org.apache.flink.api.java.io.TextInputFormat
import org.apache.flink.streaming.api.functions.source.FileProcessingMode
import org.apache.flink.api.common.io.FilePathFilter
import org.apache.flink.streaming.api.TimeCharacteristic

object App
{
    def main(args: Array[String])
    {
        val parameters = ParameterTool.fromArgs(args)
        val pagerank_iterations: Int = parameters.getRequired("pagerank_iterations").toInt
        val inputFileName = parameters.getRequired("input")
        val parallelism = parameters.getRequired("parallelism")
        val allow_latency = parameters.getRequired("allow_latency")
        val batch_size = parameters.getRequired("batch_size")
        val backfill = parameters.getRequired("backfill")

        val configuration = new Configuration;
        configuration.setString("table.exec.resource.default-parallelism", s"${parallelism}")
        configuration.setString("taskmanager.cpu.cores", s"${parallelism}")
        configuration.setString("taskmanager.memory.managed.size", "20G")
        configuration.setString("taskmanager.memory.network.max", "1G");

        configuration.setString("metrics.reporter.slf4j.factory.class", "org.apache.flink.metrics.slf4j.Slf4jReporterFactory")
        configuration.setString("metrics.reporter.slf4j.interval", "5 SECONDS")

        configuration.setString("table.exec.mini-batch.enabled", "true");
        configuration.setString("table.exec.mini-batch.allow-latency", s"${allow_latency} ms"); // we are using event time which correspond to edge id
        configuration.setString("table.exec.mini-batch.size", s"${batch_size}");
        
        configuration.setString("table.optimizer.agg-phase-strategy", "TWO_PHASE"); 
        configuration.setString("table.optimizer.incremental-agg-enabled", "true");

        val env = StreamExecutionEnvironment.createLocalEnvironment(1, configuration)
        env.setRuntimeMode(RuntimeExecutionMode.STREAMING)
        
        val tableEnv = StreamTableEnvironment.create(env, EnvironmentSettings.inStreamingMode)

        tableEnv.createTemporaryTable("SourceTable", TableDescriptor.forConnector("filesystem")
        .schema(Schema.newBuilder()
            .column("id", DataTypes.INT())
            .column("u", DataTypes.INT())
            .column("v", DataTypes.INT())
            .columnByExpression("ts", s"TO_TIMESTAMP_LTZ(IF(${backfill} >= id, 1, id), 3)")
            .watermark("ts", "ts - INTERVAL '0.001' SECOND")  // ascending timestamps watermark strategy
            .build())
        .format("json")
        .option("path", s"file:////app/data/${inputFileName}")
        .build())


        // HACK TO FORCE FLINK TO USE EVENT TIME (REQUIRED FOR MINI BATCH)
        val edgesin = tableEnv.from("SourceTable")
        val edgesin2 = tableEnv.from("SourceTable").select($"id".as("id2"), $"u".as("u2"), $"v".as("v2"), $"ts".as("ts2"))
        val edges = edgesin.join(edgesin2)
        .where($"id" === $"id2" && $"ts" === $"ts2")
        .select($"u", $"v", $"ts2")
        // .select(1.as("forcnt"), $"u", $"v", $"ts2")
        // val edges = tableEnv.from("SourceTable")

        // // Create a sink table (using SQL DDL)
        tableEnv.executeSql("CREATE TEMPORARY TABLE SinkTable (`id_rank` INT, `rank` BIGINT) WITH ('connector' = 'blackhole');")
        // tableEnv.executeSql("CREATE TEMPORARY TABLE SinkTable (`count` BIGINT) WITH ('connector' = 'print');")

        val in_vertices = edges.groupBy($"v").select($"v".as("id"), 0.as("degree0"))
        val out_vertices = edges.groupBy($"u").select($"u".as("id"), $"v".count.as("degree"))
        val degrees = in_vertices.fullOuterJoin(out_vertices.select($"id".as("id_out"), $"degree"), $"id" === $"id_out").select($"id".ifNull($"id_out").as("id"), $"degree".ifNull(0).as("degree"))
        // val base = out_vertices.select($"id").minus(in_vertices.select($"id")).select($"id", 0.as("flow"))  // minus works only in batch! Reimplementing below with join+filter
        val base = out_vertices.select($"id").leftOuterJoin(in_vertices.select($"id".as("id_in")), $"id" === $"id_in").filter($"id_in".isNull).select($"id", 0.as("flow"))
        var ranks = degrees.select($"id".as("id_rank"), 6000.as("rank"))
        
        for (_ <- 1 to pagerank_iterations) {
            var outflow = ranks.join(degrees, $"id" === $"id_rank").select($"id", ($"degree" === 0).?(0, (($"rank" * 5) / ($"degree" * 6)).floor()).as("flow"))
            var edges_flow = edges.join(outflow, $"u" === $"id").select($"v", $"flow")
            var inflows = edges_flow.groupBy($"v").select($"v".as("id"), $"flow".sum.as("flow"))
            inflows = inflows.unionAll(base)
            ranks = inflows.select($"id".as("id_rank"), ($"flow"+1000).as("rank"))
        }
        // val edge_counts = edges.groupBy($"forcnt").select($"forcnt".sum.as("count"))

        // val tableResult = edge_counts.insertInto("SinkTable").execute()
        val tableResult = ranks.insertInto("SinkTable").execute()
    }

}
