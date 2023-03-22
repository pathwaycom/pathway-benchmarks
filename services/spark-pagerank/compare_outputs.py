import sys

import numpy as np
import pandas as pd

# pathway_path = sys.argv[1]
# df_pw = pd.read_csv(pathway_path)
# ranks_pw = np.sort(df_pw["rank"].to_numpy())

pw_path = sys.argv[1]
df_pw = pd.read_csv(pw_path, sep="\t", names=["vertex", "rank"])
ranks_pw = np.sort(df_pw["rank"].to_numpy())

spark_path = sys.argv[2]
df_spark = pd.read_csv(spark_path, sep="\t", names=["vertex", "rank"])
ranks_spark = np.sort(df_spark["rank"].to_numpy())

total_eq = (ranks_pw == ranks_spark).sum()

print(df_pw[:10], df_spark[:10])
print(total_eq, ranks_pw.size, total_eq / ranks_pw.size)
print(ranks_pw[-10:], ranks_spark[-10:])
