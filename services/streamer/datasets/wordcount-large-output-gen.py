import json
import random

random.seed(1)

WORD_SIZE = 7
DICTIONARY_SIZE = 10000
TEXT_SIZE = 10000000


def generate_dictionary():
    dictionary = []
    for _ in range(DICTIONARY_SIZE):
        word = []
        for _ in range(WORD_SIZE):
            word.append(random.choice("abcdefghijklmnopqrstuvwxyz"))
        dictionary.append("".join(word))
    return dictionary


if __name__ == "__main__":
    dictionary = generate_dictionary()
    with open("wordcount-large.csv", "w") as f:
        current_dict_item_idx = 0
        for _ in range(TEXT_SIZE):
            current_word = dictionary[current_dict_item_idx]
            current_word_as_json = {"word": current_word}
            f.write(json.dumps(current_word_as_json) + "\n")
            current_dict_item_idx = (current_dict_item_idx + 1) % len(dictionary)
            if current_dict_item_idx == 0:
                f.write("*COMMIT*\n")

        f.write("*FINISH*\n")
