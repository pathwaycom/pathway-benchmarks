import json
import random
from typing import Dict

WORD_SIZE = 7
DICTIONARY_SIZE = 9000
TEXT_SIZE = 10000000

SENTINELS_COUNT = 1000
SENTINEL_PROBABILITY = 0.03


def generate_dictionary(dictionary_size):
    dictionary = set()
    for _ in range(dictionary_size):
        while True:
            word_chars = []
            for _ in range(WORD_SIZE):
                word_chars.append(random.choice("abcdefghijklmnopqrstuvwxyz"))
            word = "".join(word_chars)
            if word not in dictionary:
                break
        dictionary.add(word)
    return list(dictionary)


if __name__ == "__main__":
    dictionary_and_sentinels = generate_dictionary(DICTIONARY_SIZE + SENTINELS_COUNT)
    dictionary = dictionary_and_sentinels[:DICTIONARY_SIZE]
    sentinels = dictionary_and_sentinels[-SENTINELS_COUNT:]

    weights_since_sentinel: Dict[str, int] = {}
    word_counts: Dict[str, int] = {}

    n_negative_trajectories = 0
    sum_dictionary_word_counts = 0

    with open("weighted-wordcount-large.csv", "w") as f:
        for _ in range(TEXT_SIZE):
            is_sentinel_prob = random.random() < SENTINEL_PROBABILITY
            is_sentinel_forced = (
                sum_dictionary_word_counts == 0  # there are no words to give +1
                and n_negative_trajectories == DICTIONARY_SIZE  # we can only give -1s
            )

            is_sentinel = is_sentinel_prob or is_sentinel_forced

            if is_sentinel:
                word = random.choice(sentinels)
                weight = 1
                weights_since_sentinel = {}
                n_negative_trajectories = 0
            else:
                while True:
                    word = random.choice(dictionary)
                    if word in weights_since_sentinel:
                        weight = weights_since_sentinel[word]
                    else:
                        if word_counts.get(word, 0) == 0:
                            weight = 1
                        else:
                            weight = random.choice([-1, 1])
                    if word_counts.get(word, 0) + weight >= 0:
                        break

            if weight == -1 and word not in weights_since_sentinel:
                n_negative_trajectories += 1

            result = {
                "word": word,
                "weight": weight,
            }

            if not is_sentinel:
                weights_since_sentinel[word] = weight
                if word not in word_counts:
                    word_counts[word] = 0
                word_counts[word] += weight
                sum_dictionary_word_counts += weight

            f.write(json.dumps(result) + "\n")
