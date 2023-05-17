package com.pathway.benchmarks.kstreams.benchmarks.increment

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
    val number: Int
)

fun increment(config: Config): StreamsBuilder {
    val builder = StreamsBuilder()

    val source: KStream<String, InputModel> =
        builder.stream(config.inputTopic, Consumed.with(Serdes.String(), serde<InputModel>()))

    val wordCounts = source
        .mapValues { v -> InputModel(v.number + 1) }
        .to(config.outputTopic, Produced.with(Serdes.String(), serde<InputModel>()));

    return builder
}
