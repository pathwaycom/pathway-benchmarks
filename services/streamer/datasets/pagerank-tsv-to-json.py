import json

if __name__ == "__main__":
    is_first_row = True
    with open("soc-LiveJournal1.txt", "r") as f, open(
        "pagerank-backfill.json", "w"
    ) as fw:
        for row in f:
            if row.startswith("#"):
                continue

            tokens = row.strip().split("\t")
            assert len(tokens) == 2
            result = {"u": int(tokens[0]), "v": int(tokens[1])}
            fw.write(json.dumps(result) + "\n")
