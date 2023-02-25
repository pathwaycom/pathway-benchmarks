mod kafka_reader;
mod utils;

use kafka_reader::{get_default_kafka_config, KafkaReader, TimeLineEntry};
use utils::print_to_file;

use serde::Deserialize;
use std::env;

use itertools::Itertools;
use std::collections::BTreeMap;

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd, Deserialize)]
struct IncrementInputLine {
    number: i64,
}

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd, Deserialize)]
struct IncrementOutputLine {
    number: i64,
    pathway_time: Option<i64>,
}

fn parse_increment_input_message(json: &str) -> Option<IncrementInputLine> {
    let value: IncrementInputLine =
        serde_json::from_str(json).expect("JSON was not well-formatted");
    Some(IncrementInputLine {
        number: value.number,
    })
}

fn is_pathway_increment_header(line: String) -> bool {
    let items: Vec<&str> = line.split(',').collect();
    items[0].eq("increased_number")
}

fn parse_increment_output_message(value: &str) -> Option<IncrementOutputLine> {
    let kafka_value: Vec<&str> = value.trim().split('\n').collect();

    let line = kafka_value.last().unwrap();
    if is_pathway_increment_header(line.to_string()) {
        return None;
    }

    // let value = csv::Reader::from_reader(ms.payload().unwrap()).collect();
    let value: Vec<&str> = line.split(',').collect();

    let pathway_time: Option<i64> = if value.len() > 2 {
        Some(value[1].parse::<i64>().unwrap())
    } else {
        None
    };

    //discard pathway -1 entries
    if value.len() > 2 && value[2].eq("-1") {
        return None;
    }
    Some(IncrementOutputLine {
        number: value[0].parse::<i64>().unwrap(),
        pathway_time,
    })
}

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd)]
struct LatencyTime {
    latency: i64,
    timestamp: i64,
}

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd)]
struct TimeLatency {
    timestamp: i64,
    latency: i64,
    pathway_time: Option<i64>,
}

struct AggregatedStats {
    min: i64,
    med: i64,
    max: i64,
    count: i64,
}
fn aggregate_stats_for_batch(group: &mut dyn Iterator<Item = TimeLatency>) -> AggregatedStats {
    let mut tmp: Vec<TimeLatency> = group.collect::<Vec<TimeLatency>>();
    tmp.sort_by(|a, b| b.latency.cmp(&a.latency));
    AggregatedStats {
        min: tmp[0].latency,
        med: tmp[tmp.len() / 2].latency,
        max: tmp[tmp.len() - 1].latency,
        count: tmp.len() as i64,
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let instance_name: String = args[1].to_string();
    let metadata = instance_name.replace(['/', '-'], ",");

    let mut print_short: bool = true;
    let mut print_timeline: bool = false;
    let mut print_aggregated: bool = false;

    for i in (2..args.len()).step_by(2) {
        match args[i].as_str() {
            "--stats_short" => print_short = args[i + 1].eq("1"),
            "--stats_timeline" => print_timeline = args[i + 1].eq("1"),
            "--stats_pathway_ptime_aggregated" => print_aggregated = args[i + 1].eq("1"),
            _ => eprintln!("unknown parameter {} ", args[i].as_str()),
        }
    }

    eprintln!("Logfile path: {}", args[1]);

    let file_name = format!("results/{}-latency.txt", &instance_name);
    let timeline_file_name = format!("results/{}-timeline.txt", &instance_name);
    let aggregated_timeline_file_name =
        format!("results/{}-aggregated-timeline.txt", &instance_name);

    let kafka_reader: KafkaReader = KafkaReader {
        client_config: get_default_kafka_config(),
    };

    let timeline_input: Vec<TimeLineEntry<IncrementInputLine>> =
        kafka_reader.read_from_kafka_topic("test_0", parse_increment_input_message);

    let mut timeline_output: Vec<TimeLineEntry<IncrementOutputLine>> =
        kafka_reader.read_from_kafka_topic("test_1", parse_increment_output_message);

    timeline_output.sort();

    let mut lost_cnt = 0;
    let mut latency_profile: Vec<LatencyTime> = Vec::new();
    let mut latency_timeline: Vec<TimeLatency> = Vec::new();
    for x in &timeline_input {
        let seek: TimeLineEntry<IncrementOutputLine> = TimeLineEntry {
            timestamp: x.timestamp,
            entry: IncrementOutputLine {
                number: x.entry.number + 1,
                pathway_time: None,
            },
        };

        let res =
            timeline_output.binary_search_by(|probe| probe.entry.number.cmp(&seek.entry.number));

        let upper_b = match res {
            Ok(x) => x,
            Err(x) => x,
        };

        if upper_b == timeline_output.len() {
            //if we ever need to record lost items timestamps here is the place to plug in aggregation
            lost_cnt += 1;
        } else {
            let ub_result = &timeline_output[upper_b];
            latency_profile.push(LatencyTime {
                latency: ub_result.timestamp - x.timestamp,
                timestamp: x.timestamp,
            });
            latency_timeline.push(TimeLatency {
                timestamp: x.timestamp,
                latency: ub_result.timestamp - x.timestamp,
                pathway_time: ub_result.entry.pathway_time,
            });
        }
    }

    latency_profile.sort();
    let len = latency_profile.len();
    eprintln!("{}", &instance_name);
    for i in 0..11 {
        eprintln!(
            "{}th decile: {}ms",
            i,
            latency_profile[((len - 1) * i) / 10].latency
        );
    }
    eprintln!("Lost: {lost_cnt}");

    if print_short {
        let mut str_buffer: String = String::new();
        let relevant_percentiles = vec![0, 1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99, 100];

        for x in relevant_percentiles {
            str_buffer.push_str(&format!(
                "{},{}\n",
                x,
                latency_profile[((len - 1) * x) / 100].latency
            ));
        }
        str_buffer.push_str(&format!("{},-1,{}\n", &metadata, lost_cnt));
        print_to_file(&str_buffer, &file_name)
    }

    if print_timeline {
        let mut str_buffer: String = String::new();
        for x in &latency_timeline {
            str_buffer.push_str(&format!("{},{}\n", x.timestamp, x.latency));
        }
        print_to_file(&str_buffer, &timeline_file_name);
    }

    if print_aggregated {
        let mut str_buffer: String = String::new();
        latency_timeline.sort_by(|a, b| b.pathway_time.unwrap().cmp(&a.pathway_time.unwrap()));
        let mut tree: BTreeMap<i64, AggregatedStats> = BTreeMap::new();

        for (key, mut group) in &latency_timeline
            .into_iter()
            .group_by(|elt| (elt.pathway_time.unwrap()))
        {
            tree.insert(key, aggregate_stats_for_batch(&mut group));
        }

        for (key, x) in tree.iter() {
            str_buffer.push_str(&format!(
                "{},{},{},{},{},{}\n",
                &metadata, key, x.max, x.med, x.min, x.count
            ));
        }
        print_to_file(&str_buffer, &aggregated_timeline_file_name);
    }
}
