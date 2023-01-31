import json

DATASET_SIZE = 10000000


if __name__ == "__main__":
    with open("increment-large.json", "w") as f:
        for i in range(DATASET_SIZE):
            item = {
                "number": (i + 1),
            }
            f.write("{}\n".format(json.dumps(item)))
