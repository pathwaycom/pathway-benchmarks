mod kafka_reader;
mod utils;
use kafka_reader::{get_default_kafka_config, KafkaReader, TimeLineEntry};
use std::fs::File;
use std::io::{BufRead, BufReader};
use utils::print_to_file;

use serde::Deserialize;
use std::collections::HashMap;
use std::env;

use itertools::Itertools;
use std::collections::BTreeMap;

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd, Deserialize)]
struct WordCountInputLine {
    word: String,
}

fn parse_wordcount_input_message(json: &str) -> Option<WordCountInputLine> {
    if json == "*FINISH*" || json == "*COMMIT*" {
        None
    } else {
        let ret: WordCountInputLine = serde_json::from_str(json)
            .unwrap_or_else(|_| panic!("JSON was not well-formatted: {json}"));
        Some(ret)
    }
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

    // handle pathway delta
    if value.len() == 4 && (value[3].eq("-1")) {
        return None;
    }

    //handle flink delta
    if value.len() == 3 && value[2].eq("-D") {
        return None;
    }

    //TODO: if we get more weird output formats
    // we should change parsing method depending on stat-collector parameter
    // now we only have two unusual cases to handle, we can look at length of a row

    if value.len() < 2 {
        eprintln!("Suspicious value: {value:?}");
    }

    let pathway_time: Option<i64> = if value.len() == 4 {
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

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd, Clone)]
struct LatencyTime {
    latency: i64,
    timestamp: i64,
}

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd, Clone)]
struct TimeLatency {
    timestamp: i64,
    latency: i64,
    pathway_time: Option<i64>,
}

#[derive(Debug, Eq, Ord, PartialEq, PartialOrd)]
struct AggregatedStats {
    min: i64,
    p05: i64,
    med: i64,
    p95: i64,
    max: i64,
    count: i64,
}
fn aggregate_stats_for_batch(group: &mut dyn Iterator<Item = TimeLatency>) -> AggregatedStats {
    let mut tmp: Vec<TimeLatency> = group.collect::<Vec<TimeLatency>>();
    tmp.sort_by(|a, b| b.latency.cmp(&a.latency));
    AggregatedStats {
        min: tmp[0].latency,
        p05: tmp[tmp.len() / 20].latency,
        med: tmp[tmp.len() / 2].latency,
        p95: tmp[tmp.len() * 19 / 20].latency,
        max: tmp[tmp.len() - 1].latency,
        count: tmp.len() as i64,
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let instance_prefix_no_engine_version: String = args[1].to_string();
    let mut instance_suffix: String = "unknown".to_string();
    let mut print_short: bool = true;
    let mut print_timeline: bool = false;
    let mut print_pathway_time_aggregated: bool = false;
    let mut print_time_aggregated: bool = false;
    let mut skip_prefix_length: usize = 0;
    for i in (2..args.len()).step_by(2) {
        match args[i].as_str() {
            "--stats-short" => print_short = args[i + 1].eq("1"),
            "--stats-timeline" => print_timeline = args[i + 1].eq("1"),
            "--stats-pathway-ptime-aggregated" => {
                print_pathway_time_aggregated = args[i + 1].eq("1")
            }
            "--stats-time-aggregated" => print_time_aggregated = args[i + 1].eq("1"),
            "--skip-prefix-length" => skip_prefix_length = args[i + 1].parse().unwrap(),
            "--instance-suffix" => instance_suffix = args[i + 1].parse().unwrap(),
            _ => eprintln!("unknown parameter {} ", args[i].as_str()),
        }
    }

    // handle pw engine version;
    let mut pw_version = "NA".to_string();
    if instance_prefix_no_engine_version.contains("pathway") {
        let file = File::open("results/pw-version.txt").unwrap();
        let mut string_line = "pathway, version UNKNOWN".to_string();
        for line in BufReader::new(file).lines() {
            string_line = line.unwrap().to_string();
            eprintln!("{}", string_line);
        }
        pw_version = string_line
            .strip_prefix("pathway, version ")
            .unwrap_or(&format!("local.{}", &string_line))
            .to_string();
    }

    let instance_prefix = format!("{}-{}", &instance_prefix_no_engine_version, &pw_version);

    let metadata_pref = instance_prefix.replace(['/', '-'], ",");
    let metadata_suff = instance_suffix.replace(['-'], ",");

    let instance_name = format!("{}-{}", &instance_prefix, &instance_suffix);

    let file_name = format!("results/{}-latency.csv", &instance_name);
    let timeline_file_name = format!("results/{}-timeline.csv", &instance_name);
    let aggregated_timeline_file_name =
        format!("results/{}-aggregated-timeline.csv", &instance_name);
    let pref_aggregated_timeline_file_name =
        format!("results/{}-pref-aggregated-timeline.csv", &instance_name);

    let aggregated_pw_timeline_file_name =
        format!("results/{}-ptime-aggregated-timeline.csv", &instance_name);

    let mut timeline_input: Vec<TimeLineEntry<WordCountInputLine>> = {
        let kafka_reader: KafkaReader = KafkaReader {
            client_config: get_default_kafka_config(),
        };
        kafka_reader.read_from_kafka_topic("test_0", parse_wordcount_input_message)
    };

    let mut timeline_output: Vec<TimeLineEntry<WordCountOutputLine>> = {
        let kafka_reader: KafkaReader = KafkaReader {
            client_config: get_default_kafka_config(),
        };
        kafka_reader.read_from_kafka_topic("test_1", parse_wordcount_output_message)
    };

    timeline_input.sort();

    let mut word_count: Vec<InputWithCount> = Vec::new();
    let mut counts: HashMap<String, i64> = HashMap::new();

    for input_line in timeline_input {
        counts
            .entry(input_line.entry.word.clone())
            .and_modify(|counter| *counter += 1)
            .or_insert(1);

        word_count.push(InputWithCount {
            timestamp: input_line.timestamp,
            word: input_line.entry.word.clone(),
            count: *counts.get(&input_line.entry.word).unwrap(),
        });
    }

    timeline_output.sort();

    let mut time_counts: HashMap<String, Vec<CountAndTime>> = HashMap::new();
    for output_line in timeline_output {
        time_counts
            .entry(output_line.entry.word.clone())
            .and_modify(|vector| {
                vector.push(CountAndTime {
                    count: output_line.entry.count,
                    timestamp: output_line.timestamp,
                    pathway_time: output_line.entry.pathway_time,
                })
            })
            .or_default();
    }

    let mut lost_cnt = 0;
    let mut latency_profile: Vec<LatencyTime> = Vec::new();
    let mut latency_timeline: Vec<TimeLatency> = Vec::new();

    for x in &word_count {
        let time_counts_x = time_counts.get(&x.word);
        if time_counts_x.is_none() {
            lost_cnt += 1;
            continue;
        }
        let time_counts_x = time_counts_x.unwrap();
        let res = time_counts_x.binary_search(&CountAndTime {
            count: x.count,
            timestamp: x.timestamp,
            pathway_time: None,
        });
        let upper_b = match res {
            Ok(x) => x,
            Err(x) => x,
        };

        if upper_b == time_counts_x.len() {
            //if we ever need to record lost items timestamps here is the place to plug in aggregation
            lost_cnt += 1;
        } else {
            let ub_result = &time_counts_x[upper_b];
            latency_profile.push(LatencyTime {
                latency: ub_result.timestamp - x.timestamp,
                timestamp: x.timestamp,
            });
            latency_timeline.push(TimeLatency {
                timestamp: x.timestamp,
                latency: ub_result.timestamp - x.timestamp,
                pathway_time: ub_result.pathway_time,
            });
        }
    }
    let mut trimmed_latency_profile = latency_profile[skip_prefix_length..].to_vec();
    trimmed_latency_profile.sort();

    let len = trimmed_latency_profile.len();
    eprintln!("{}", &instance_name);
    for i in 0..11 {
        eprintln!(
            "{}th decile: {} ms",
            i,
            trimmed_latency_profile[((len - 1) * i) / 10].latency
        );
    }
    eprintln!("lost {lost_cnt} ");

    if print_short {
        let mut str_buffer: String = String::new();
        let relevant_percentiles = vec![0, 1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99, 100];

        for x in relevant_percentiles {
            str_buffer.push_str(&format!(
                "{},{},{},{}\n",
                &metadata_pref,
                &metadata_suff,
                x,
                trimmed_latency_profile[((len - 1) * x) / 100].latency
            ));
        }
        str_buffer.push_str(&format!(
            "{},{},-1,{}\n",
            &metadata_pref, &metadata_suff, lost_cnt
        ));
        print_to_file(&str_buffer, &file_name)
    }

    if print_timeline {
        let mut str_buffer: String = String::new();
        for x in &latency_timeline[skip_prefix_length..] {
            str_buffer.push_str(&format!("{},{}\n", x.timestamp, x.latency));
        }
        print_to_file(&str_buffer, &timeline_file_name);
    }

    if print_time_aggregated {
        let mut trimmed_lt = latency_timeline[skip_prefix_length..].to_vec();

        trimmed_lt.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
        let mut tree: BTreeMap<i64, AggregatedStats> = BTreeMap::new();

        for (key, mut group) in &trimmed_lt.into_iter().group_by(|elt| (elt.timestamp)) {
            tree.insert(key, aggregate_stats_for_batch(&mut group));
        }
        let mut str_buffer: String = String::new();
        for (key, x) in tree.iter() {
            str_buffer.push_str(&format!(
                "{},{},{},{},{},{},{},{},{}\n",
                &metadata_pref, &metadata_suff, key, x.max, x.p95, x.med, x.p05, x.min, x.count
            ));
        }

        print_to_file(&str_buffer, &aggregated_timeline_file_name);
    }

    if print_time_aggregated {
        let mut trimmed_lt = latency_timeline[0..skip_prefix_length].to_vec();

        trimmed_lt.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
        let mut tree: BTreeMap<i64, AggregatedStats> = BTreeMap::new();

        for (key, mut group) in &trimmed_lt.into_iter().group_by(|elt| (elt.timestamp)) {
            tree.insert(key, aggregate_stats_for_batch(&mut group));
        }
        let mut str_buffer: String = String::new();
        for (key, x) in tree.iter() {
            str_buffer.push_str(&format!(
                "{},{},{},{},{},{},{},{},{}\n",
                &metadata_pref, &metadata_suff, key, x.max, x.p95, x.med, x.p05, x.min, x.count
            ));
        }

        print_to_file(&str_buffer, &pref_aggregated_timeline_file_name);
    }

    if print_pathway_time_aggregated {
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
                "{},{},{},{},{},{},{},{},{}\n",
                &metadata_pref, &metadata_suff, key, x.max, x.p95, x.med, x.p05, x.min, x.count
            ));
        }

        print_to_file(&str_buffer, &aggregated_pw_timeline_file_name);
    }
}
