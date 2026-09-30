from pathlib import Path
from airq import load_raw, clean_row, FIELDS

OUT_DIR = Path("out")
OUT_FILE = OUT_DIR / "bars.txt"

def make_bar(value, max_len=40):
    if value is None:
        return ""
    length = int(value / max(FIELDS, key=lambda f: 1) * max_len)
    return "#" * length

def main():
    rows = [clean_row(r) for r in load_raw()]
    rows = [r for r in rows if r]
    
    OUT_DIR.mkdir(exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for row in rows:
            date = row["date"]
            f.write(f"{date}\n")
            for field in FIELDS:
                val = row.get(field)
                bar = make_bar(val)
                f.write(f"  {field}: {bar} {val}\n")
            f.write("\n")

if __name__ == "__main__":
    main()