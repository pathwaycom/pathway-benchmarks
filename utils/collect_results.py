import os
from typing import Dict, List


def read_tokens(first_token, path):
    with open(path, "r") as f:
        tokens = f.read().split(",")
    tokens = [first_token] + tokens
    return tokens


if __name__ == "__main__":
    data: Dict[str, List] = {}
    results = os.listdir("../docker-compose/results/")
    for fname in results:
        if not fname.endswith("-latency.txt"):
            continue
        tokens = fname[:-4].split("-")
        task_instance = "{}-latency-{}".format(tokens[0], tokens[1])
        if task_instance not in data:
            data[task_instance] = []
        data[task_instance].append(
            read_tokens(tokens[2], "../docker-compose/results/{}".format(fname))
        )

    for k, v in data.items():
        v.sort(key=lambda x: int(x[0]))
        with open("../results/{}.csv".format(k), "w") as f:
            f.write("rps,diff_begin,diff_end,diff_max\n")
            for entry in v:
                f.write("{}\n".format(",".join(entry)))
