package com.pathway.benchmarks.kstreams

import mu.KotlinLogging
import com.pathway.benchmarks.kstreams.Config
import org.apache.kafka.streams.StreamsConfig
import com.pathway.benchmarks.kstreams.benchmarks.wordcount.wordcount
import com.pathway.benchmarks.kstreams.benchmarks.increment.increment
import kotlin.system.exitProcess
import java.util.*
import java.util.concurrent.CountDownLatch
import org.apache.kafka.streams.KafkaStreams
import org.apache.kafka.common.serialization.Serdes


val logger = KotlinLogging.logger {}

fun main() {
    val config = Config()
    logger.info(config.toString())

    val props = Properties().apply {
        put(StreamsConfig.APPLICATION_ID_CONFIG, config.groupId)
        put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, config.kafkaBootstrapServers)
        put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.String().javaClass)
        put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.String().javaClass)
        put(StreamsConfig.COMMIT_INTERVAL_MS_CONFIG, config.autoCommitFrequency)
        put(StreamsConfig.NUM_STREAM_THREADS_CONFIG, config.numStreamThreads)

    }

    val builder = when (config.benchmarkType) {
        "wordcount" -> wordcount(config)
        "increment" -> increment(config)
        else -> {
            throw RuntimeException("Unknown benchmark type: ${config.benchmarkType}")
        }
    }

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