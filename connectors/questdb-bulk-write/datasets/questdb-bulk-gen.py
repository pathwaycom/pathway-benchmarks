"""Generate a sharded CSV dataset for the QuestDB bulk-write benchmark.

One row = a 64-bit key, a short string, a float, and a boolean. The rows are
split across ``--shards`` CSV files in ``--output-dir`` so that a multi-worker
Pathway run can read (and write) them in parallel. The directory is mounted
read-only into the Pathway container.
"""

import argparse
import os

import numpy as np
import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="questdb bulk-write dataset generator")
    parser.add_argument("--rows", type=int, default=20_000_000)
    parser.add_argument("--shards", type=int, default=64)
    parser.add_argument("--output-dir", type=str, required=True)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    rng = np.random.default_rng(1)
    ids = np.arange(args.rows, dtype=np.int64)
    for shard, shard_ids in enumerate(np.array_split(ids, args.shards)):
        df = pd.DataFrame(
            {
                "k": shard_ids,
                "name": "item_" + pd.Series(shard_ids).astype(str),
                "value": rng.random(len(shard_ids)),
                "flag": rng.integers(0, 2, len(shard_ids)).astype(bool),
            }
        )
        df.to_csv(os.path.join(args.output_dir, f"part_{shard:03d}.csv"), index=False)
    print(f"wrote {args.rows} rows across {args.shards} shards to {args.output_dir}")
