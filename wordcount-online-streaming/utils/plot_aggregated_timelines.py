import os

import matplotlib.pyplot as plt
import pandas as pd

columns = [
    "framework",
    "benchmark",
    "run_timestamp",
    "workers",
    "cores",
    "batch_ms",
    "-",
    "throughput",
    "--",
    "version(code)",
    "version(engine)",
    "dict_size",
    "skip_prefix_length",
    "wait_time_ms",
    "recorded_dataset_size",
    "timestamp",
    "max-latency",
    "p95",
    "med-latency",
    "p05",
    "min-latency",
    "count",
]

results_dir, *file_tree_listed = os.walk("../results/")
for (dir_path, dir_names, file_names) in file_tree_listed:
    engine = dir_path.split("/")[-1]
    print(engine + "\n")
    print(file_names)

    for name in [x for x in file_names if "aggregated" in x]:
        timeline_df = pd.read_csv(
            f"../results/{engine}/{name}",
            names=columns,
            header=None,
        )
        fig, ax = plt.subplots()
        # timeline_df.plot.scatter(
        #     x="timestamp",
        #     y="min-latency",
        #     color="green",
        #     ax=ax,
        #     style=".",
        #     s=0.5,
        #     linewidths=0,
        # )

        timeline_df.plot.scatter(
            x="timestamp",
            y="med-latency",
            color="blue",
            ax=ax,
            style=".",
            s=1,
            linewidths=0,
        )
        # timeline_df.plot.scatter(
        #     x="timestamp",
        #     y="max-latency",
        #     color="red",
        #     ax=ax,
        #     style=".",
        #     s=0.5,
        #     linewidths=0,
        # )

        timeline_df.plot.scatter(
            x="timestamp",
            y="count",
            color="black",
            ax=ax.twinx(),
            style=".",
            s=0.5,
            linewidths=0,
        )
        png_name = name.replace(".csv", ".png")
        plt.savefig(
            f"{engine}_{png_name}",
            dpi=600,
        )
