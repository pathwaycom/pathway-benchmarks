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
    let mut dataset_path: String = String::from("");
    let mut messages_per_second = 100000;
    let mut skip_prefix_length: u64 = 0;
    let mut wait_time_ms: u64 = 0;
    let mut emit_interval_ms = 10;
    let args: Vec<String> = env::args().collect();

    for i in (1..args.len()).step_by(2) {
        match args[i].as_str() {
            "--dataset-path" => dataset_path = args[i + 1].to_string(),
            "--messages-per-second" => messages_per_second = args[i + 1].parse().unwrap(),
            "--skip-prefix-length" => skip_prefix_length = args[i + 1].parse().unwrap(),
            "--wait-time-ms" => wait_time_ms = args[i + 1].parse().unwrap(),
            "--emit-interval-ms" => emit_interval_ms = args[i + 1].parse().unwrap(),
            _ => eprintln!("unknown parameter {} ", args[i].as_str()),
        }
    }
    emit_interval_ms += messages_per_second / 100000;
    // on small throughputs we want to send messages more often
    // the factor at the ent essentially says what is the send interval (in ms)
    // tested for 300k throughput, 5 seems too low, 10 seem to have a fairly high margin
    let batch_s = (messages_per_second / 1000) * emit_interval_ms;

    let mut client_config = ClientConfig::new();
    client_config.set("group.id", "$GROUP_NAME");
    if env::var("USING_BENCHMARK_HARNESS").unwrap_or("0".to_string()) == "1" {
        client_config.set("bootstrap.servers", "kafka:9092");
    } else {
        client_config.set("bootstrap.servers", "localhost:9092");
    }
    client_config.set("enable.partition.eof", "false");
    client_config.set("session.timeout.ms", "60000");
    client_config.set("enable.auto.commit", "true");
    //the one below is questionble - the general idea is to trigger actual send at every batch
    client_config.set("queue.buffering.max.messages", batch_s.to_string());
    client_config.set("queue.buffering.max.ms", emit_interval_ms.to_string());
    let producer: BaseProducer = client_config.create().unwrap();

    //more like time to send 1000 messages, to hit 1 second after messages per second
    //name sleep_after_each_1000_mcs is confusing, should be something that denotes the length of a block
    //(mps / 1000) blocklen = 1000000

    let sleep_after_each_1000_mcs = 1_000_000_000 / messages_per_second;

    let threshold_1 = skip_prefix_length / 8;
    let mut threshold_2 = skip_prefix_length / 4;
    let mut threshold_3 = skip_prefix_length / 2;
    let mut threshold_4 = skip_prefix_length;
    let mut warm_up = true;

    let mut n_sent = 0;
    let file = File::open(dataset_path).unwrap();

    let start_time = Instant::now();
    let mut offs = 0;
    for line in BufReader::new(file).lines() {
        let line_to_send = line.unwrap();
        let mut entry = BaseRecord::to("test_0").payload(&line_to_send).key("");
        loop {
            match producer.send(entry) {
                Err((
                    KafkaError::MessageProduction(RDKafkaErrorCode::QueueFull),
                    nonsent_entry,
                )) => {
                    producer.poll(Duration::from_millis(0));
                    entry = nonsent_entry;
                    continue;
                }
                Err(e) => panic!("Unexpected kind of error: {e:?}"),
                Ok(_) => break,
            }
        }

        n_sent += 1;
        if n_sent % batch_s == 0 {
            let time_passed = start_time.elapsed();
            let time_expected = Duration::from_micros(sleep_after_each_1000_mcs * n_sent / 1000);
            if time_expected > time_passed {
                eprintln!("Need to sleep for {:?} more", time_expected - time_passed);
                sleep(time_expected - time_passed);
            } else {
                eprint!(".")
            }
            // non zero offs reduces throughput
            if warm_up {
                n_sent += offs;
                threshold_2 += offs;
                threshold_3 += offs;
                threshold_4 += offs;

                if n_sent >= threshold_1 && n_sent < threshold_2 && offs == 0 {
                    eprintln!("Break to unload initial queue");
                    sleep(Duration::from_millis(wait_time_ms));
                    n_sent += wait_time_ms * messages_per_second / 1000;
                    threshold_2 += wait_time_ms * messages_per_second / 1000;
                    threshold_3 += wait_time_ms * messages_per_second / 1000;
                    threshold_4 += wait_time_ms * messages_per_second / 1000;
                    offs = batch_s / 2;
                }
                if n_sent >= threshold_2 && n_sent < threshold_3 && offs == batch_s / 2 {
                    eprintln!("speed_up_1");
                    offs = batch_s / 4;
                }
                if n_sent >= threshold_3 && n_sent < threshold_4 && offs == batch_s / 4 {
                    eprintln!("speed_up_2");
                    offs = 0;
                }
                if n_sent >= threshold_4 {
                    eprintln!("begin test run!");
                    warm_up = false;
                }
            }
        }
    }

    producer.flush(Timeout::Never).unwrap();

    eprintln!("Time spent on streaming: {:?}", start_time.elapsed());
}
