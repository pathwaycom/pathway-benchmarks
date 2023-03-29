import json

LEAVE_ONLY_X_LINES = 5000000
BACKFILLING_START = 4500000
BACKFILLING_STEP = 1000

if __name__ == "__main__":
    is_first_row = True
    lines_written = 0
    with open("soc-LiveJournal1.txt", "r") as f, open(
        "pagerank-5m-backfill.json", "w"
    ) as fw:
        for row in f:
            if row.startswith("#"):
                continue

            tokens = row.strip().split("\t")
            assert len(tokens) == 2
            result = {"u": int(tokens[0]), "v": int(tokens[1])}
            fw.write(json.dumps(result) + "\n")

            lines_written += 1
            if (
                lines_written >= BACKFILLING_START
                and (lines_written - BACKFILLING_START) % BACKFILLING_STEP == 0
            ):
                fw.write("*COMMIT*\n")

            if lines_written == LEAVE_ONLY_X_LINES:
                break
