package com.pathway.benchmarks.kstreams

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.apache.kafka.common.serialization.Deserializer
import org.apache.kafka.common.serialization.Serde
import org.apache.kafka.common.serialization.Serializer

inline fun <reified T : Any> deserializer(): Deserializer<T> {
    return Deserializer<T> { _, payload -> Json.decodeFromString(String(payload)) }
}

inline fun <reified T : Any> serializer(): Serializer<T> {
    return Serializer<T> { _, payload: T -> Json.encodeToString(payload).toByteArray() }
}

inline fun <reified T: Any> serde(): Serde<T> {
    return object: Serde<T> {
        override fun serializer() = serializer<T>()
        override fun deserializer() = deserializer<T>()
    }
}
