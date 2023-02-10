import matplotlib.pyplot as plt
import pandas as pd

columns = ["timestamp", "latency"]
timeline_df = pd.read_csv(
    "../docker-compose/results/pathway/wordcount-1675986444.044187-1-1-10-5-111111-unaware-timeline.txt",
    names=columns,
    header=None,
)
timeline_df.plot.scatter(x="timestamp", y="latency", style=".", s=1)
plt.savefig(
    "graph.png",
    dpi=600,
)
