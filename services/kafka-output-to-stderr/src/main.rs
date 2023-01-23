use rand::Rng;
use rdkafka::consumer::{BaseConsumer, Consumer, DefaultConsumerContext};
use rdkafka::{ClientConfig, Message, Offset, TopicPartitionList};
use std::str::from_utf8;
use std::time::Duration;

/*
    This program reads from kafka input / output topics, and prints it to stderr.
    Use for development, debug and test of other services or as a starting-point template for more complex stat-collectors.
*/

fn get_kafka_config() -> ClientConfig {
    let mut rng = rand::thread_rng();
    let group_id: u32 = rng.gen();

    eprintln!("Using consumer group id: {}", group_id);

    let mut client_config = ClientConfig::new();
    client_config
        .set("group.id", "rust-final-consumer")
        .set("bootstrap.servers", "kafka:9092")
        .set("enable.partition.eof", "false")
        .set("session.timeout.ms", "60000")
        .set("enable.auto.commit", "true")
        .set("auto.offset.reset", "earliest");
    client_config
}

fn get_messages(topic_name: &str) {
    eprintln!("getting messages from {}", topic_name);
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

    loop {
        let poll = consumer.poll(Duration::from_secs(1));
        if let Some(ms_wrapped) = poll {
            let ms = ms_wrapped.unwrap();
            match topic_name {
                "test_0" => eprintln!("in {:?}", from_utf8(ms.payload().unwrap()).unwrap()),
                "test_1" => eprintln!("out {:?}", from_utf8(ms.payload().unwrap()).unwrap()),
                _ => (),
            }
        } else {
            eprintln!("none for topic {}", topic_name);
            break;
        }
    }
}

fn main() {
    get_messages("test_0");
    get_messages("test_1");
}
