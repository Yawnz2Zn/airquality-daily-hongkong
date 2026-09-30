# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///
from pathlib import Path
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from airq import load_clean

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "plot.png"

FIELDS = ["pm25", "pm10", "o3", "no2", "so2", "co"]
TITLES = {
    "pm25": "PM2.5 (Fine particles)",
    "pm10": "PM10 (Coarse particles)",
    "o3": "Ozone",
    "no2": "Nitrogen dioxide",
    "so2": "Sulphur dioxide",
    "co": "Carbon monoxide",
}

def main():
    rows = load_clean()
    by_month = defaultdict(lambda: defaultdict(list))
    for r in rows:
        key = r["date"].strftime("%Y-%m")
        for f in FIELDS:
            by_month[key][f].append(r[f])

    months = sorted(by_month)

    fig, axes = plt.subplots(2, 3, figsize=(15, 8), constrained_layout=True)

    for ax, field in zip(axes.flat, FIELDS):
        means = [sum(by_month[m][field]) / len(by_month[m][field]) for m in months]
        ax.plot(months, means, marker="o", linewidth=1.2, markersize=4, color="#1f77b4")
        ax.set_title(TITLES[field], fontsize=12, fontweight="bold")
        ax.set_ylabel(field.upper(), fontsize=10)
        ax.tick_params(axis="x", rotation=60, labelsize=8)
        ax.grid(True, linestyle="--", alpha=0.4)

    fig.suptitle("Hong Kong Air Quality – Monthly Averages (raw daily data)", fontsize=16, fontweight="bold")

    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=200)
    print("saved:", OUT)

if __name__ == "__main__":
    main()