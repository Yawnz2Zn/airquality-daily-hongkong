# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Read data/hongkong-air-quality.csv and turn it into numbers.

One year: 2025. One row per day.

    uv run airq.py     -- prints the first row, one value, its type
"""

from datetime import date
from pathlib import Path
import csv

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "hongkong-air-quality.csv"

FIELDS = ["pm25", "pm10", "o3", "no2", "so2", "co"]
YEAR = 2025

# PM2.5 is a subset of PM10, so it can never be bigger. The file has the two
# columns the wrong way round -- 360 of 362 days disagreed before this was on.
SWAP_PM = True


def clean(r):
    """One line of the CSV -> one day of numbers, or None if it will not parse."""
    try:
        y, m, d = (int(x) for x in r["date"].strip().split("/"))
        day = date(y, m, d)
    except (ValueError, KeyError, AttributeError):
        return None

    out = {"date": day}
    for f in FIELDS:
        try:
            out[f] = float(r[f])
        except (ValueError, KeyError, TypeError):
            out[f] = None

    if SWAP_PM and out["pm25"] is not None and out["pm10"] is not None:
        out["pm25"], out["pm10"] = out["pm10"], out["pm25"]

    return out if out["pm25"] is not None else None


def load_clean():
    """Every day of 2025 that has a PM2.5 reading, in order."""
    days = {}
    with open(RAW, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            c = clean({k.strip(): v for k, v in r.items() if k})
            if c and c["date"].year == YEAR and c["date"] not in days:
                days[c["date"]] = c
    return [days[d] for d in sorted(days)]


def monthly_means(rows, field="pm25"):
    sums = [0.0] * 12
    counts = [0] * 12
    for r in rows:
        if r[field] is not None:
            m = r["date"].month - 1
            sums[m] += r[field]
            counts[m] += 1
    return [s / c if c else None for s, c in zip(sums, counts)]


if __name__ == "__main__":
    MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    rows = load_clean()
    print("first row: ", rows[0])
    print("one value: ", rows[0]["pm25"], type(rows[0]["pm25"]).__name__)
    print("days:      ", len(rows), f"({rows[0]['date']} to {rows[-1]['date']})")

    bad = [r for r in rows if r["pm10"] and r["pm25"] > r["pm10"]]
    print("pm25 > pm10 on", len(bad), "day(s) — should be 0")

    print("\nmonthly mean PM2.5:")
    for name, v in zip(MONTHS, monthly_means(rows)):
        bar = "#" * round(v / 3) if v else ""
        print(f"  {name}  {bar:<40} {v:.1f}")

