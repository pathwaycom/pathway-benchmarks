import json
import random

random.seed(1)

WORD_SIZE = 7
DICTIONARY_SIZE = 10000
TEXT_SIZE = 10000000
COMMIT_EVERY_LINES = None


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
        lines_written = 0
        for _ in range(TEXT_SIZE):
            current_word = random.choice(dictionary)
            current_word_as_json = {"word": current_word}
            f.write(json.dumps(current_word_as_json) + "\n")
            lines_written += 1
            if COMMIT_EVERY_LINES and lines_written % COMMIT_EVERY_LINES == 0:
                f.write("*COMMIT*\n")
