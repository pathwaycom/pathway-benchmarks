use std::env;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::thread::sleep;
use std::time::Duration;
use std::time::Instant;

use rdkafka::error::{KafkaError, RDKafkaErrorCode};
use rdkafka::producer::{BaseProducer, BaseRecord, Producer};
use rdkafka::util::Timeout;
use rdkafka::ClientConfig;

fn main() {
    let (dataset_path, messages_per_second) = {
        let args: Vec<String> = env::args().collect();
        if args.len() != 3 {
            panic!("You need to specify exactly two arguments: dataset path and streaming speed");
        }
        let rps: u64 = args[2].parse().unwrap();
        (&args[1].to_string(), rps)
    };

    let mut client_config = ClientConfig::new();
    client_config.set("group.id", "$GROUP_NAME");
    client_config.set("bootstrap.servers", "kafka:9092");
    client_config.set("enable.partition.eof", "false");
    client_config.set("session.timeout.ms", "60000");
    client_config.set("enable.auto.commit", "true");

    let producer: BaseProducer = client_config.create().unwrap();

    //more like time to send 1000 messages, to hit 1 second after messages per second
    //name sleep_after_each_1000_mcs is confusing, should be something that denotes the length of a block
    //(mps / 1000) blocklen = 1000000

    let sleep_after_each_1000_mcs = 1_000_000_000 / messages_per_second;

    let mut n_sent = 0;
    let file = File::open(dataset_path).unwrap();

    let start_time = Instant::now();

    for line in BufReader::new(file).lines() {
        let line_to_send = line.unwrap();
        let mut entry = BaseRecord::to("test_0").payload(&line_to_send).key("");
        loop {
            match producer.send(entry) {
                Err((
                    KafkaError::MessageProduction(RDKafkaErrorCode::QueueFull),
                    nonsent_entry,
                )) => {
                    producer.poll(Duration::from_millis(10));
                    entry = nonsent_entry;
                    continue;
                }
                Err(e) => panic!("Unexpected kind of error: {e:?}"),
                Ok(_) => break,
            }
        }

        n_sent += 1;
        if n_sent % 5000 == 0 {
            let time_passed = start_time.elapsed();
            let time_expected = Duration::from_micros(sleep_after_each_1000_mcs * (n_sent / 1000));
            if time_expected > time_passed {
                eprintln!("Need to sleep for {:?} more", time_expected - time_passed);
                sleep(time_expected - time_passed);
            }
        }
    }

    producer.flush(Timeout::Never).unwrap();

    eprintln!("Time spent on streaming: {:?}", start_time.elapsed());
}
