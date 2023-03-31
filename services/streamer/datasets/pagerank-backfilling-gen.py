import argparse
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PageRank backfilling dataset generator"
    )
    parser.add_argument(
        "--original-dataset-path", type=str, default="soc-LiveJournal1.txt"
    )
    parser.add_argument("--output-path", type=str, required=True)
    parser.add_argument("--total-lines", type=int, required=True)
    parser.add_argument("--backfilling-start", type=int, required=True)
    parser.add_argument("--backfilling-step", type=int, required=True)
    args = parser.parse_args()

    is_first_row = True
    lines_written = 0
    with open(args.original_dataset_path, "r") as f, open(args.output_path, "w") as fw:
        for row in f:
            if row.startswith("#"):
                continue

            tokens = row.strip().split("\t")
            assert len(tokens) == 2
            result = {"u": int(tokens[0]), "v": int(tokens[1])}
            fw.write(json.dumps(result) + "\n")

            lines_written += 1

            is_backfilling_started = lines_written >= args.backfilling_start
            is_end_of_block = (
                lines_written - args.backfilling_start
            ) % args.backfilling_step == 0

            if is_backfilling_started and is_end_of_block:
                fw.write("*COMMIT*\n")

            if lines_written == args.total_lines:
                break
