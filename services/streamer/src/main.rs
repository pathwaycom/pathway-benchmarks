use std::env;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::thread::sleep;
use std::time::Duration;
use std::time::Instant;

use rdkafka::producer::{BaseProducer, BaseRecord, Producer};
use rdkafka::util::Timeout;
use rdkafka::ClientConfig;

fn main() {
    let (dataset_path, messages_per_second) = {
        let args: Vec<String> = env::args().collect();
        if args.len() != 3 {
            panic!("You need to specify exactly one argument, which is the dataset path");
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

    let sleep_after_each_1000_mcs = 1_000_000_000 / messages_per_second;

    let mut n_sent = 0;
    let file = File::open(dataset_path).unwrap();

    let start_time = Instant::now();
    for line in BufReader::new(file).lines() {
        producer
            .send(BaseRecord::to("test_0").payload(&line.unwrap()).key(""))
            .unwrap();

        n_sent += 1;
        if n_sent % 5000 == 0 {
            producer.flush(Timeout::Never).unwrap();

            let time_passed = start_time.elapsed();
            let time_expected = Duration::from_micros(sleep_after_each_1000_mcs * (n_sent / 1000));
            if time_expected > time_passed {
                eprintln!("Need to sleep for {:?} more", time_expected - time_passed);
                sleep(time_expected - time_passed);
            }
        }
    }

    producer.flush(Timeout::Never).unwrap();
}
