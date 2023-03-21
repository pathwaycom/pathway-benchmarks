import os

# todos
# -- parametrize streamer window size
# -- make this script up to date
# -- add grouping by commit-window-size (filtering it is)
# make python script for all the experiments
# set up new experiments (mostly for pathway and vanilla flink,
#   as those don't have any queued attempts on improvements)

# to do later:
# add speed ramp-up for streamer? (a little bit annoying,
#   but can be done by artificially inflating n_sent)
# test flink tableapi without streaming api for io
# test spark wordcount without tableapi (should be easy in scala)
# make kstreams commit windows behave (if possible at all)
# write some content on benchmarks
# # introduce wordcount benchmark
# # --  state pathways stats (low latency to around 300k, slightly higher latency
#   puts us at better throughput),
# # -- (ongoing) methodology - define latency
# # methodology - discuss batch sizes
# # methodology - discuss dictionary size
# # methodology - disclaimers on fine tuning
# # methodology - disclaimers on local environment
# # detailed comparison (for each of them - latency-throughput plot and a low
#       throughput-latency plot, for 2 windows (if windowed))
# # # pathway section
# # # flink section
# # # spark section
# # # kstreams section


def squash_aggregates(metadata, file_location):
    f = open(f"../docker-compose/results/{file_location}")
    ret = ""
    for line in f.readlines():
        data = line.split(",")[-1].rstrip("\n")
        ret += f",{data}"
    return f"{metadata},5000{ret}\n"


def main():
    (_, engines, _), *file_tree_listed = os.walk("../docker-compose/results/")

    aggr_total = open(
        "../docker-compose/results/aggregated-aggregates.csv",
        "w+",
    )

    aggr_total.write(
        "engine,benchmark,timestamp,workers,cores,batch_length_ms,_,throughput,_,dict_size,"
        + "min,p01,p05,p10,p20,p30,p40,median,p60,p70,p80,p90,p95,p99,max,lost\n"
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
                "engine,benchmark,timestamp,workers,cores,batch_length_ms,_,throughput,_,"
                + "min,p01,p05,p10,p20,p30,p40,median,p60,p70,p80,p90,p95,p99,max,lost\n"
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
