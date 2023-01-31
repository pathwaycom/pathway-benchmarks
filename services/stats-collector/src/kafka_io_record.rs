mod kafka_reader;
mod utils;

use kafka_reader::{get_default_kafka_config, KafkaReader, TimeLineEntry};
use utils::print_to_file;

use serde::Deserialize;

/*
    This program reads from kafka input / output topics, and prints it to stderr.
    Use for development, debug and test of other services or as a starting-point template for more complex stat-collectors.
*/

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd, Deserialize)]
struct KafkaValue {
    value: String,
}

fn parse_message(json: &str) -> Option<KafkaValue> {
    let ret: KafkaValue = KafkaValue {
        value: json.to_string(),
    };
    Some(ret)
}

fn print_all_messages(messages: &Vec<TimeLineEntry<KafkaValue>>, stream_file_name: &str) {
    let mut str_buffer: String = String::new();
    for x in messages {
        str_buffer.push_str(&format!("{},{}\n", x.timestamp, x.entry.value));
    }
    print_to_file(&str_buffer, stream_file_name);
}

fn main() {
    let kafka_reader: KafkaReader = KafkaReader {
        client_config: get_default_kafka_config(),
    };

    let timeline_input: Vec<TimeLineEntry<KafkaValue>> =
        kafka_reader.read_from_kafka_topic("test_0", parse_message);

    let timeline_output: Vec<TimeLineEntry<KafkaValue>> =
        kafka_reader.read_from_kafka_topic("test_1", parse_message);

    print_all_messages(&timeline_input, "results/kafka_io_record/in");
    print_all_messages(&timeline_output, "results/kafka_io_record/out");
}
