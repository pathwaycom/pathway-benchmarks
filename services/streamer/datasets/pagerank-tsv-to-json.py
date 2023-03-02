import json

if __name__ == "__main__":
    is_first_row = True
    with open("pagerank.tsv", "r") as f, open("pagerank.json", "w") as fw:
        for row in f:
            if is_first_row:
                is_first_row = False
                continue
            tokens = row.strip().split("\t")
            assert len(tokens) == 3
            result = {"u": int(tokens[1]), "v": int(tokens[2])}
            fw.write(json.dumps(result) + "\n")
