from datetime import date
from pathlib import Path
import csv

DATA_DIR = Path("data")
RAW = DATA_DIR / "hongkong-air-quality.csv"
FIELDS = ["pm25", "pm10", "o3", "no2", "so2", "co"]


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

def clean_row(r):
    d = parse_date(r.get("date", ""))
    if d is None:
        return None
    out = {"date": d}
    for field in FIELDS:
        raw = (r.get(field) or "").strip()
        if not raw:
            return None
        try:
            v = float(raw)
        except ValueError:
            return None
        if v < 0:
            return None
        out[field] = v
    return out


def load_clean():
    seen, rows = set(), []
    for r in load_raw():
        c = clean_row(r)
        if c is None:
            continue
        if c["date"] in seen:
            continue
        seen.add(c["date"])
        rows.append(c)
    rows.sort(key=lambda x: x["date"])
    return rows


def bar(value, scale=0.5):
    n = 0 if value is None else round(value * scale)
    return "#" * max(0, n)


def grade(pm25):
    if pm25 is None:
        return "na"
    if pm25 <= 35: return "优"
    if pm25 <= 75: return "良"
    if pm25 <= 115: return "轻度"
    if pm25 <= 150: return "中度"
    if pm25 <= 250: return "重度"
    return "严重"