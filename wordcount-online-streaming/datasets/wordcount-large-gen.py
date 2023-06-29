import argparse
import json
import os
import random

random.seed(1)

WORD_SIZE = 7


def generate_dictionary(dict_size):
    dictionary = []
    for _ in range(dict_size):
        word = []
        for _ in range(WORD_SIZE):
            word.append(random.choice("abcdefghijklmnopqrstuvwxyz"))
        dictionary.append("".join(word))
    return dictionary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="wordcount test generator")
    parser.add_argument("--dict-size", type=int, required=False, default=5000)
    parser.add_argument("--dataset-size", type=int, required=False, default=76000000)
    args = parser.parse_args()

    dictionary = generate_dictionary(args.dict_size)
    path = os.path.join(os.path.dirname(__file__), "wordcount-large.csv")
    with open(path, "w") as f:
        lines_written = 0
        for _ in range(args.dataset_size):
            current_word = random.choice(dictionary)
            current_word_as_json = {"word": current_word}
            f.write(json.dumps(current_word_as_json) + "\n")
            lines_written += 1
