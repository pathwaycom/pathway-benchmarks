package com.pathway.benchmarks.kstreams.wordcount

import mu.KotlinLogging
import org.apache.kafka.common.serialization.Serdes
import org.apache.kafka.streams.KafkaStreams
import org.apache.kafka.streams.StreamsBuilder
import org.apache.kafka.streams.StreamsConfig
import org.apache.kafka.streams.kstream.*
import java.util.*
import java.util.concurrent.CountDownLatch
import kotlin.system.exitProcess
import com.pathway.benchmarks.kstreams.Config
import com.pathway.benchmarks.kstreams.serde
import org.apache.kafka.streams.kstream.Materialized;
import kotlinx.serialization.*

val logger = KotlinLogging.logger {}

@Serializable
class InputModel {
    var word: String = ""
}

fun main() {
    val config = Config()

    logger.info(config.toString())

    val props = Properties().apply {
        put(StreamsConfig.APPLICATION_ID_CONFIG, config.groupId)
        put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, config.kafkaBootstrapServers)
        put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().javaClass)
        put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().javaClass)
        put(StreamsConfig.COMMIT_INTERVAL_MS_CONFIG, config.autoCommitFrequency)
    }

    val builder = StreamsBuilder()

    val source: KStream<String, InputModel> =
            builder.stream(config.inputTopic, Consumed.with(Serdes.String(), serde<InputModel>()))

    val wordCounts = source
            .groupBy { _, v -> v.word }
            .count()
            .mapValues { k, v -> "$k,$v" }

    wordCounts.toStream().to(config.outputTopic, Produced.with(Serdes.String(), Serdes.String()));

    val streams = KafkaStreams(builder.build(), props)
    val latch = CountDownLatch(1)

    Runtime.getRuntime().addShutdownHook(object : Thread() {
        override fun run() {
            streams.close()
            latch.countDown()
        }
    })

    try {
        streams.cleanUp()
        streams.start()
        latch.await()
    } catch (e: Throwable) {
        exitProcess(1)
    }
    exitProcess(0)
}
