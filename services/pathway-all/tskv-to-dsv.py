if __name__ == "__main__":
    with open("results.tskv", "r") as f, open("results8.csv", "w") as fw:
        for row in f:
            data = [token.split("=")[1] for token in row.strip().split("\t")]
            fw.write(",".join(data) + "\n")
