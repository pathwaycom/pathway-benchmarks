import os

BENCHMARKS = [
    "increment",
    "pagerank",
    "wordcount",
]

ENGINES = [
    "spark",
    "pathway",
]

PATHWAY_ENGINE_NAME = "pathway"


def read_tokens(first_token, path):
    with open(path, "r") as f:
        tokens = f.read().split(",")
    tokens = [first_token] + tokens
    return tokens


def render_time_unaware_results(engine_name, benchmark_type):
    folder_path = "../docker-compose/results/{}/".format(engine_name)
    raw_result_logs = os.listdir(folder_path)
    data_points = {}

    for log_name in raw_result_logs:
        if not log_name.startswith(benchmark_type):
            continue
        if not log_name.endswith("-unaware-latency.txt"):
            continue
        tokens = log_name.split("-")
        rate = tokens[2]
        data_points[rate] = read_tokens(rate, os.path.join(folder_path, log_name))

    data_points_unique = []
    for _, data_point in data_points.items():
        data_points_unique.append(data_point)

    data_points_unique.sort(key=lambda x: int(x[0]))
    with open(
        "../results/{}/{}-unaware.csv".format(benchmark_type, engine_name), "w"
    ) as f:
        f.write("rps,diff_begin,diff_end,diff_max\n")
        for entry in data_points_unique:
            f.write("{}\n".format(",".join(entry)))


def render_time_aware_pathway_results(benchmark_type):
    folder_path = "../docker-compose/results/pathway/"
    raw_result_logs = os.listdir(folder_path)
    data_points = {}

    for log_name in raw_result_logs:
        if not log_name.startswith(benchmark_type):
            continue
        if log_name.endswith("-unaware-latency.txt") or not log_name.endswith(
            "-latency.txt"
        ):
            continue
        tokens = log_name.split("-")

        commit_frequency = tokens[1]
        rate = tokens[2]

        if commit_frequency not in data_points:
            data_points[commit_frequency] = []
        data_points[commit_frequency].append(
            read_tokens(rate, os.path.join(folder_path, log_name))
        )

    for commit_frequency, stats in data_points.items():
        stats.sort(key=lambda x: int(x[0]))
        with open(
            "../results/{}/pathway-{}.csv".format(benchmark_type, commit_frequency), "w"
        ) as f:
            f.write("rps,diff_begin,diff_end,diff_max\n")
            for entry in stats:
                f.write("{}\n".format(",".join(entry)))


def render_pathway_results(benchmark_type):
    render_time_unaware_results(PATHWAY_ENGINE_NAME, benchmark_type)
    render_time_aware_pathway_results(benchmark_type)


def render_non_native_results(benchmark_type, engine_name):
    render_time_unaware_results(engine_name, benchmark_type)


if __name__ == "__main__":
    for benchmark_type in BENCHMARKS:
        for engine_name in ENGINES:
            if engine_name == PATHWAY_ENGINE_NAME:
                render_pathway_results(benchmark_type)
            else:
                render_non_native_results(benchmark_type, engine_name)
