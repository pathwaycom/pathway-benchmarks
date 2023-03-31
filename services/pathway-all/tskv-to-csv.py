import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TSKV to CSV")
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    with open(args.input, "r") as f, open(args.output, "w") as fw:
        for row in f:
            data = [token.split("=")[1] for token in row.strip().split("\t")]
            fw.write(",".join(data) + "\n")
