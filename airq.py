# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Parse the raw file into numbers. This is the only file that reads the CSV.

Every other script starts with `from airq import load_clean` -- your own file is
a library too, and this is what that sentence means in practice.

Run it on its own to check the parse before you draw anything:

    uv run airq.py
"""

from datetime import date
from pathlib import Path
import csv

# HERE is the folder this file is in; data/ is an address built from it, so the
# script works no matter which folder you run it from.
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
RAW = DATA_DIR / "hongkong-air-quality.csv"

FIELDS = ["pm25", "pm10", "o3", "no2", "so2", "co"]

# A day with no PM2.5 is not a day we can draw. The other five may be missing --
# see the note in the README about what that costs.
REQUIRED = ["pm25"]

# ---- knob -----------------------------------------------------------------
# Which years to draw. This one line is the only thing you need to touch.
#
#   2025          one year  -> 12 calendar rows, and every tile really is one day
#   [2024, 2025]  two years -> 24 calendar rows, still one day per tile
#   None          every year in the file (2014-2026), which pools thirteen
#                 Januaries into one tile -- the seasonal cycle survives, the
#                 thirteen-year decline does not
#
# plot.py and heatmap.py both call load_clean(), so this changes both at once.
YEAR = 2025


def parse_date(s):
    s = s.strip()
    parts = s.split("/")
    if len(parts) != 3:
        return None
    try:
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return date(y, m, d)
    except ValueError:
        return None


def load_raw():
    rows = []
    with open(RAW, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append({k.strip(): v for k, v in r.items()})
    return rows


def clean(r):
    """One raw row -> (one clean row, why it was dropped). Exactly one of the two."""
    d = parse_date(r.get("date", ""))
    if d is None:
        return None, "no readable date"
    out = {"date": d}
    for field in FIELDS:
        raw = (r.get(field) or "").strip()
        if not raw:
            out[field] = None           # not measured, not zero
            continue
        try:
            v = float(raw)
        except ValueError:
            out[field] = None
            continue
        out[field] = None if v < 0 else v   # a negative reading is a sensor fault
    missing = [f for f in REQUIRED if out[f] is None]
    if missing:
        return None, "missing " + ", ".join(missing)
    return out, None


def clean_row(r):
    """Same as clean(), without the reason. Kept so older callers still work."""
    return clean(r)[0]


def load_reported(year=None):
    """(clean rows, rows that were dropped and why). Use this in the terminal."""
    years = year if year is not None else YEAR
    if isinstance(years, int):
        years = [years]
    seen, rows, skipped = set(), [], []
    for i, r in enumerate(load_raw(), start=1):
        c, why = clean(r)
        if c is None:
            skipped.append((i, why))
            continue
        if c["date"] in seen:
            skipped.append((i, "duplicate date"))
            continue
        if years is not None and c["date"].year not in years:
            continue
        seen.add(c["date"])
        rows.append(c)
    rows.sort(key=lambda x: x["date"])
    return rows, skipped


def load_clean(year=None):
    """Just the rows. This is what plot.py and heatmap.py import."""
    return load_reported(year)[0]


def grid_months(rows):
    """The (year, month) pairs present, in order -- 12 for one year, 24 for two."""
    seen, out = set(), []
    for r in rows:
        key = (r["date"].year, r["date"].month)
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def grid_labels(rows, short=True):
    """Row labels for the calendar: 'Jan' for one year, 'Jan 24' for several."""
    months = grid_months(rows)
    many = len({y for y, _ in months}) > 1
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    if not many:
        return [names[m - 1] for _, m in months]
    return [f"{names[m - 1]} {str(y)[2:]}" for y, m in months]


def bar(value, scale=0.5):
    n = 0 if value is None else round(value * scale)
    return "#" * max(0, n)


def grade(pm25):
    if pm25 is None:
        return "no data"
    if pm25 <= 35:
        return "excellent"
    if pm25 <= 75:
        return "good"
    if pm25 <= 115:
        return "lightly polluted"
    if pm25 <= 150:
        return "moderately polluted"
    if pm25 <= 250:
        return "heavily polluted"
    return "severely polluted"


def monthly_means(rows, field="pm25"):
    """One number per month out of every day in it."""
    sums = [0.0] * 12
    counts = [0] * 12
    for r in rows:
        v = r[field]
        if v is None:
            continue
        m = r["date"].month - 1
        sums[m] += v
        counts[m] += 1
    return [s / c if c else None for s, c in zip(sums, counts)]


def yearly_means(rows, field="pm25"):
    """[(year, mean), ...] -- the trend across the whole file."""
    sums, counts = {}, {}
    for r in rows:
        v = r[field]
        if v is None:
            continue
        y = r["date"].year
        sums[y] = sums.get(y, 0.0) + v
        counts[y] = counts.get(y, 0) + 1
    return [(y, sums[y] / counts[y]) for y in sorted(sums)]


if __name__ == "__main__":
    MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    print("raw file:", RAW, f"({RAW.stat().st_size / 1024:.0f} KB)")
    raw = load_raw()
    print("rows in the file:", len(raw))
    print("columns:", list(raw[0].keys()))

    rows, skipped = load_reported()
    print("\nfirst clean row:", rows[0])
    one = rows[0]["pm25"]
    print("one value:", one, type(one).__name__)
    print("coverage:  %s -> %s   (%d days, %.1f years)"
          % (rows[0]["date"], rows[-1]["date"], len(rows),
             (rows[-1]["date"] - rows[0]["date"]).days / 365.25))

    print(f"\nkept {len(rows)} day(s); skipped {len(skipped)} row(s):")
    for i, why in skipped[:8]:
        print(f"  row {i}: {why}")
    if len(skipped) > 8:
        print(f"  ... and {len(skipped) - 8} more")

    # A sanity check that is worth running on any air-quality file: PM2.5 is a
    # subset of PM10, so it can never be larger. If it is, the columns are not
    # what we think they are.
    bad = [r for r in rows
           if r["pm10"] is not None and r["pm25"] > r["pm10"]]
    if bad:
        print(f"\n!! {len(bad)} day(s) where PM2.5 > PM10 — physically impossible.")
        print("   first:", bad[0]["date"], "pm25", bad[0]["pm25"], "pm10", bad[0]["pm10"])
        print("   check the column order in the raw file before you trust this.")

    print("\nyearly mean PM2.5 (the trend):")
    for y, v in yearly_means(rows):
        print(f"  {y}  {bar(v, 0.25):<42} {v:.1f}")

    print("\nmonthly mean PM2.5 (the seasonal cycle, all years pooled):")
    for name, v in zip(MONTHS, monthly_means(rows)):
        print(f"  {name}  {bar(v, 0.25):<42}"
              + ("-" if v is None else f"{v:.1f}"))
