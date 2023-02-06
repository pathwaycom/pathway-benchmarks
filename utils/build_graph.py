import matplotlib.pyplot as plt
import pandas as pd

columns = ["timestamp", "latency"]
timeline_df = pd.read_csv(
    "../docker-compose/results/pathway/weighted_wordcount-1675438571.4078279-1-1-100-5-150000-unaware-timeline.txt",
    names=columns,
    header=None,
)
timeline_df.plot.scatter(x="timestamp", y="latency", style=".", s=1)
plt.savefig(
    "graph.png",
    dpi=600,
)
