import json
import sys

if __name__ == "__main__":
    is_first_row = True
    input_path = sys.argv[1]
    ext = input_path.split(".")[-1]
    output_path = input_path[: -len(ext)] + "jl"
    id = 0
    with open(input_path, "r") as f, open(output_path, "w") as fw:
        for row in f:
            tokens = row.strip().split("\t")
            assert len(tokens) == 2
            id += 1
            result = {"id": str(id), "u": tokens[0], "v": tokens[1]}
            fw.write(json.dumps(result) + "\n")
