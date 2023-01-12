use rand::Rng;
use std::cmp::max;
use std::env;
use std::fs::File;
use std::io::Write;
use std::time::Duration;

use rdkafka::consumer::{BaseConsumer, Consumer, DefaultConsumerContext};
use rdkafka::{ClientConfig, Message, Offset, Timestamp, TopicPartitionList};

fn get_kafka_config() -> ClientConfig {
    let mut rng = rand::thread_rng();
    let group_id: u32 = rng.gen();

    eprintln!("Using consumer group id: {}", group_id);

    let mut client_config = ClientConfig::new();
    client_config
        .set("group.id", group_id.to_string())
        .set("bootstrap.servers", "kafka:9092")
        .set("enable.partition.eof", "false")
        .set("session.timeout.ms", "60000")
        .set("enable.auto.commit", "true")
        .set("auto.offset.reset", "earliest");
    client_config
}

fn get_timeline_attempt(topic_name: &str) -> Vec<i64> {
    let client_config = get_kafka_config();

    let consumer: BaseConsumer<DefaultConsumerContext> =
        client_config.create().expect("Couldn't create consumer");
    consumer
        .subscribe(&[topic_name])
        .expect("Failed to subscribe to topic");

    let metadata = consumer
        .fetch_metadata(Some(topic_name), None)
        .expect("Failed to fetch metadata");
    let mut tpl = TopicPartitionList::new();
    for topic in metadata.topics() {
        eprintln!("topic {}", topic.name());
        for partition in topic.partitions() {
            eprintln!("topic {} has partition {}", topic.name(), partition.id());
            tpl.add_partition_offset(topic.name(), partition.id(), Offset::Beginning)
                .expect("Addition to TPL failed");
        }
    }
    consumer
        .assign(&tpl)
        .expect("Consumer asssignment has failed");
    consumer
        .seek(topic_name, 0, Offset::Offset(0), None)
        .expect("Seek failed");

    let mut timeline = Vec::new();
    let mut seconds_waiting = 0;
    loop {
        let message = consumer.poll(Duration::from_secs(1));
        if let Some(message) = message {
            if let Timestamp::CreateTime(timestamp) =
                message.expect("Failed to get message").timestamp()
            {
                timeline.push(timestamp);
            } else {
                eprintln!("WARNING: There is no CreateTime in message");
            }
        } else {
            if !timeline.is_empty() {
                eprintln!("No more messages left at the length {}", timeline.len());
                break;
            }
            seconds_waiting += 1;
            if seconds_waiting == 10 {
                eprintln!("Max waiting time expired, retrying...");
                return timeline;
            }
        }
    }

    eprintln!("Timeline size: {}", timeline.len());
    timeline
}

fn get_timeline(topic_name: &str) -> Vec<i64> {
    loop {
        let timeline = get_timeline_attempt(topic_name);
        if !timeline.is_empty() {
            return timeline;
        }
    }
}

fn main() {
    let instance_name = {
        let args: Vec<String> = env::args().collect();
        if args.len() != 2 {
            panic!("You need to specify exactly one argument, which is the resulting file path");
        }
        eprintln!("Logfile path: {}", args[1]);
        format!("results/{}-latency.txt", &args[1].to_string())
    };

    let timeline_input = get_timeline("test_0");
    let timeline_output = get_timeline("test_1");
    eprintln!(
        "Timeline (input) consists of {} events",
        timeline_input.len()
    );
    eprintln!(
        "Timeline (output) consists of {} events",
        timeline_output.len()
    );

    let last_timestamps_difference =
        timeline_output[timeline_output.len() - 1] - timeline_input[timeline_input.len() - 1];
    let first_timestamps_difference = timeline_output[0] - timeline_input[0];

    let mut max_timings_diff = 0;
    for i in 0..timeline_input.len() {
        let mut j: usize = i * timeline_output.len() / timeline_input.len();
        if j >= timeline_output.len() {
            j = timeline_output.len() - 1;
        }
        let timestamps_diff = (timeline_output[j] - timeline_input[i]).abs();
        max_timings_diff = max(max_timings_diff, timestamps_diff);
    }

    eprintln!(
        "Timestamps difference in the beginning: {}",
        first_timestamps_difference
    );
    eprintln!(
        "Timestamps difference in the end: {}",
        last_timestamps_difference
    );
    eprintln!("Timestamps difference max: {}", max_timings_diff);

    let mut file = File::create(instance_name).expect("Failed to create log file");
    file.write_all(
        format!(
            "{},{},{}",
            first_timestamps_difference, last_timestamps_difference, max_timings_diff
        )
        .as_bytes(),
    )
    .expect("Log writing failed");
}
