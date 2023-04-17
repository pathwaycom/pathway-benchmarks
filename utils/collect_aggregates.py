import os


def squash_aggregates(metadata, file_location):
    f = open(f"../docker-compose/results/{file_location}")
    ret = ""
    for line in f.readlines():
        data = line.split(",")[-1].rstrip("\n")
        ret += f",{data}"

    m_cols = metadata.split(",")
    return f"{','.join(m_cols[:10])}{ret},{','.join(m_cols[10:])}\n"


def main():
    (_, engines, _), *file_tree_listed = os.walk("../docker-compose/results/")

    aggr_total = open(
        "../docker-compose/results/aggregated-aggregates.csv",
        "w+",
    )

    aggr_total.write(
        "engine,benchmark,timestamp,workers,cores,batch_length_ms,_,throughput,_,version(code),version(engine)"
        + ",min,p01,p05,p10,p20,p30,p40,median,p60,p70,p80,p90,p95,p99,max,lost"
        + ",dict_size,skip_prefix_length,wait_time_ms,recorded_dataset_size\n"
    )

    for (dir_path, dir_names, file_names) in file_tree_listed:
        engine = dir_path.split("/")[-1]
        print(engine + "\n")
        print(file_names)

        with open(
            f"../docker-compose/results/{engine}/aggregated-aggregates.csv",
            "w+",
        ) as f:
            f.write(
                "engine,benchmark,timestamp,workers,cores,batch_length_ms,_,throughput,_version(code),version(engine)"
                + ",min,p01,p05,p10,p20,p30,p40,median,p60,p70,p80,p90,p95,p99,max,lost"
                + ",skip_prefix_length,wait_time_ms,recorded_dataset_size\n"
            )
            for name in [x for x in file_names if "latency" in x]:
                metadata = (
                    f"{engine},{name.replace('-', ',').replace(',latency.csv', '')}"
                )
                file_location = f"{engine}/{name}"
                line = squash_aggregates(metadata, file_location)
                f.write(line)
                aggr_total.write(line)


if __name__ == "__main__":
    main()
