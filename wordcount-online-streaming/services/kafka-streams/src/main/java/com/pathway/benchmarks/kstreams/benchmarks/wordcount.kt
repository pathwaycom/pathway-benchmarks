package com.pathway.benchmarks.kstreams.benchmarks.wordcount

import mu.KotlinLogging
import org.apache.kafka.streams.StreamsBuilder
import org.apache.kafka.common.serialization.Serdes
import org.apache.kafka.streams.kstream.*
import com.pathway.benchmarks.kstreams.Config
import com.pathway.benchmarks.kstreams.serde
import kotlinx.serialization.*

val logger = KotlinLogging.logger {}

@Serializable
data class InputModel(
    val word: String
)

fun wordcount(config: Config): StreamsBuilder {
    val builder = StreamsBuilder()

    val source: KStream<String, InputModel> =
            builder.stream(config.inputTopic, Consumed.with(Serdes.String(), serde<InputModel>()))

    val wordCounts = source
            .groupBy { _, v -> v.word }
            .count()
            .mapValues { k, v -> "$k,$v" }
            .toStream()
            .to(config.outputTopic, Produced.with(Serdes.String(), Serdes.String()));

    return builder
}
