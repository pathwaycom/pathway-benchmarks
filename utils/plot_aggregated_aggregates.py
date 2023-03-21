import os

import matplotlib.pyplot as plt
import pandas as pd

metadata = [
    "framework",
    "benchmark",
    "run_timestamp",
    "workers",
    "cores",
    "batch_length_ms",
    "we_should_skip_this",
    "throughput",
    "don't-need-that-either",
    "dict_size",
]

percentiles = [
    "min",
    "p01",
    "p05",
    "p10",
    "p20",
    "p30",
    "p40",
    "median",
    "p60",
    "p70",
    "p80",
    "p90",
    "p95",
    "p99",
    "max",
    "lost",
]

columns = metadata + percentiles

results_dir, *file_tree_listed = os.walk("../docker-compose/results/")

batch_sizes = [5, 10, 20, 50]

for (dir_path, dir_names, file_names) in file_tree_listed:
    engine = dir_path.split("/")[-1]
    print(engine + "\n")
    print(file_names)

    collected_aggregates = pd.read_csv(
        f"../docker-compose/results/{engine}/aggregated-aggregates.csv",
        names=columns,
        header=None,
        skiprows=1,
    )

    for batch_s in batch_sizes:
        print(collected_aggregates)
        filtered = collected_aggregates[
            collected_aggregates["batch_length_ms"] == batch_s
        ]
        filtered = filtered.sort_values("throughput")
        print(filtered.size)
        if filtered.size == 0:
            continue
        # fig, ax = plt.subplots(
        # timeline_df.plot.scatter(
        #     x="timestamp",
        #     y="min-latency",
        #     color="green",
        #     ax=ax,
        #     style=".",
        #     s=0.5,
        #     linewidths=0,
        # )

        filtered.plot(
            x="throughput",
            y=["median", "p95"],
            color="br",
        )
        plt.savefig(
            f"{engine}-{batch_s}-latency-throughput-pref-350k.png",
            dpi=600,
        )
