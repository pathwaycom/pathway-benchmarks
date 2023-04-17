package com.pathway.benchmarks.kstreams

const val KAFKA_BOOTSTRAP_SERVERS = "KAFKA_BOOTSTRAP_SERVERS"
const val APPLICATION_ID = "APPLICATION_ID"
const val INPUT_TOPIC = "INPUT_TOPIC"
const val OUTPUT_TOPIC = "OUTPUT_TOPIC"
const val AUTOCOMMIT_FREQUENCY_MS = "AUTOCOMMIT_FREQUENCY_MS"
const val BENCHMARK_TYPE = "BENCHMARK_TYPE"
const val CORES = "CORES"

data class Config(
        val kafkaBootstrapServers: String = env(KAFKA_BOOTSTRAP_SERVERS, "kafka:9092"),
        val groupId: String = env(APPLICATION_ID, "kafka-streams-benchmark"),
        val inputTopic: String = env(INPUT_TOPIC, "test_0"),
        val outputTopic: String = env(OUTPUT_TOPIC, "test_1"),
        val autoCommitFrequency: String = env(AUTOCOMMIT_FREQUENCY_MS, "10000"),
        val benchmarkType: String = env(BENCHMARK_TYPE, "wordcount"),
        val numStreamThreads: String = env(CORES, "1")
)

fun env(name: String, defaultValue: String): String {
    return System.getenv(name) ?: defaultValue
}
