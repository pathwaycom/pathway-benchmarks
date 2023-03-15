mod kafka_reader;
mod utils;

use kafka_reader::{get_default_kafka_config, KafkaReader, TimeLineEntry};
use utils::print_to_file;

use serde::Deserialize;
use std::collections::HashMap;
use std::env;

use itertools::Itertools;
use std::collections::BTreeMap;

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd, Deserialize)]
struct WordCountInputLine {
    word: String,
    weight: Option<i64>,
}

fn parse_wordcount_input_message(json: &str) -> Option<WordCountInputLine> {
    let ret: WordCountInputLine = serde_json::from_str(json).expect("JSON was not well-formatted");
    Some(ret)
}

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd)]
struct WordCountOutputLine {
    word: String,
    count: i64,
    pathway_time: Option<i64>,
}

fn is_pathway_word_count_header(line: String) -> bool {
    let items: Vec<&str> = line.split(',').collect();
    items[0].eq("word") && items[1].eq("count")
}

fn strip_quotes_if_present(word: String) -> String {
    let mut from = 0;
    let mut to = word.len();

    if word.as_bytes()[0] as char == '"' {
        from += 1;
    }

    if word.as_bytes()[word.len() - 1] as char == '"' {
        to -= 1;
    }
    word[from..to].to_string()
}
fn parse_wordcount_output_message(csv: &str) -> Option<WordCountOutputLine> {
    let kafka_value: Vec<&str> = csv.trim().split('\n').collect();
    let line = kafka_value.last().unwrap();
    if is_pathway_word_count_header(line.to_string()) {
        return None;
    }

    let value: Vec<&str> = line.split(',').collect();

    if value[3].eq("-1") {
        return None;
    }

    let pathway_time: Option<i64> = if value.len() > 2 {
        Some(value[2].parse::<i64>().unwrap())
    } else {
        None
    };

    Some(WordCountOutputLine {
        word: strip_quotes_if_present(value[0].to_string()),
        count: value[1].parse::<i64>().unwrap(),
        pathway_time,
    })
}

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd)]
struct InputWithCount {
    timestamp: i64,
    word: String,
    count: i64,
}

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd)]
struct CountAndTime {
    count: i64,
    timestamp: i64,
    pathway_time: Option<i64>,
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

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd)]
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
            "--stats-short" => print_short = args[i + 1].eq("1"),
            "--stats-timeline" => print_timeline = args[i + 1].eq("1"),
            "--stats-pathway-ptime-aggregated" => print_aggregated = args[i + 1].eq("1"),
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

    let timeline_input: Vec<TimeLineEntry<WordCountInputLine>> =
        kafka_reader.read_from_kafka_topic("test_0", parse_wordcount_input_message);

    let timeline_output: Vec<TimeLineEntry<WordCountOutputLine>> =
        kafka_reader.read_from_kafka_topic("test_1", parse_wordcount_output_message);

    for i in 0..timeline_output.len() - 1 {
        assert!(timeline_output[i].timestamp <= timeline_output[i + 1].timestamp);
    }
    eprintln!(
        "Timeline order checks passed. Timeline length: {}",
        timeline_output.len()
    );

    let mut counts: HashMap<String, i64> = HashMap::new();
    let mut input_pair_indices: HashMap<(String, i64), Vec<usize>> = HashMap::new();
    for (index, input_line) in timeline_input.iter().enumerate() {
        let weight = input_line.entry.weight.unwrap_or(1);

        counts
            .entry(input_line.entry.word.clone())
            .and_modify(|counter| *counter += weight)
            .or_insert(weight);

        let word = input_line.entry.word.clone();
        let count = *counts.get(&input_line.entry.word).unwrap();

        input_pair_indices
            .entry((word, count))
            .and_modify(|indices| indices.push(index))
            .or_insert_with(|| vec![index]);
    }

    let mut output_pair_indices: HashMap<(String, i64), Vec<usize>> = HashMap::new();
    for (index, output_line) in timeline_output.iter().enumerate() {
        let word = output_line.entry.word.clone();
        let count = output_line.entry.count;

        output_pair_indices
            .entry((word, count))
            .and_modify(|indices| indices.push(index))
            .or_insert_with(|| vec![index]);
    }

    let mut matched_indices = 0;

    let mut completion_timestamp: Vec<Option<(i64, i64)>> = vec![None; timeline_input.len()];
    for (key, input_indices) in input_pair_indices.into_iter() {
        match output_pair_indices.get(&key) {
            Some(output_indices) => {
                if input_indices.len() == output_indices.len() {
                    matched_indices += input_indices.len();
                    for (input_idx, output_idx) in input_indices.iter().zip(output_indices) {
                        assert!(completion_timestamp[*input_idx].is_none());
                        completion_timestamp[*input_idx] = Some((
                            timeline_output[*output_idx].timestamp,
                            timeline_output[*output_idx].entry.pathway_time.unwrap(),
                        ));
                    }
                }
            }
            None => continue,
        }
    }

    eprintln!("Total matched: {matched_indices} indices");

    let mut last_seen_completion_timestamp = None;
    for maybe_completion_timestamp in completion_timestamp.iter_mut().rev() {
        if let Some(_completion_timestamp) = maybe_completion_timestamp {
            last_seen_completion_timestamp = *maybe_completion_timestamp;
        }
        *maybe_completion_timestamp = last_seen_completion_timestamp;
    }

    let mut lost_cnt = 0;
    let mut latency_profile: Vec<LatencyTime> = Vec::new();
    let mut latency_timeline: Vec<TimeLatency> = Vec::new();

    for (index, input_line) in timeline_input.iter().enumerate() {
        let completed_at = completion_timestamp[index];

        if let Some((completed_at, pathway_time)) = completed_at {
            latency_profile.push(LatencyTime {
                latency: completed_at - input_line.timestamp,
                timestamp: input_line.timestamp,
            });

            latency_timeline.push(TimeLatency {
                timestamp: completed_at,
                latency: completed_at - input_line.timestamp,
                pathway_time: Some(pathway_time),
            });
        } else {
            lost_cnt += 1;
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
                "{},{},{}\n",
                &metadata,
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
