use rand::Rng;
use std::str::from_utf8;

use std::time::Duration;

use rdkafka::consumer::{BaseConsumer, Consumer, DefaultConsumerContext};
use rdkafka::message::BorrowedMessage;
use rdkafka::{ClientConfig, Message, Offset, TopicPartitionList};

pub fn get_default_kafka_config() -> ClientConfig {
    let mut rng = rand::thread_rng();
    let group_id: u32 = rng.gen();

    eprintln!("Using consumer group id: {group_id}");

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

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct TimeLineEntry<K> {
    pub timestamp: i64,
    pub entry: K,
}

pub struct KafkaReader {
    pub client_config: ClientConfig,
}

impl KafkaReader {
    fn get_topic_consumer(&self, topic_name: &str) -> BaseConsumer<DefaultConsumerContext> {
        let consumer: BaseConsumer<DefaultConsumerContext> = self
            .client_config
            .create()
            .expect("Couldn't create consumer");
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
            .expect("Consumer assignment has failed");
        consumer
            .seek(topic_name, 0, Offset::Offset(0), None)
            .expect("Seek failed");

        consumer
    }

    fn parse_kafka_entry<K>(
        &self,
        ms: &BorrowedMessage,
        parse: fn(&str) -> Option<K>,
    ) -> Option<K> {
        parse(from_utf8(ms.payload().unwrap()).unwrap())
    }

    // using parser that returns Option<K> allows to handle situation when
    // a framework sends some extra meta-messages or handle some other quirks,
    //by returning none, when the message does no correspond to a valid line of input dataset
    pub fn read_from_kafka_topic<K>(
        &self,
        topic_name: &str,
        parse: fn(&str) -> Option<K>,
    ) -> Vec<TimeLineEntry<K>> {
        let consumer = self.get_topic_consumer(topic_name);
        let mut timeline: Vec<TimeLineEntry<K>> = Vec::new();
        let mut seconds_waiting = 0;
        while timeline.is_empty() {
            loop {
                let message = consumer.poll(Duration::from_secs(1));
                if let Some(Result::Ok(message)) = message {
                    if let Some(entry) = self.parse_kafka_entry(&message, parse) {
                        timeline.push(TimeLineEntry {
                            timestamp: message.timestamp().to_millis().unwrap(),
                            entry,
                        });
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
        }
        timeline
    }
}
