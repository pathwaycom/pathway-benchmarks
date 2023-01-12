import json
import random

DATASET_SIZE = 10000000


if __name__ == "__main__":
    with open("increment-large.json", "w") as f:
        for _ in range(DATASET_SIZE):
            item = {
                "number": random.randrange(0, 1000000000 + 1),
            }
            f.write("{}\n".format(json.dumps(item)))
