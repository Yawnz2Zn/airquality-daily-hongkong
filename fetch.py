# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""Get the raw file once. Keep it. Never ask twice.

The rule for this assignment is fetch once, keep the file, parse the file. This
script is the "fetch once" half of it:

  1. look for the file in data/;
  2. if it is not there, ask for it once, with a User-Agent that says who we are;
  3. write the reply to data/ unchanged -- no parsing, no tidying, no re-encoding;
  4. on every later run, do nothing at all.

data/ is committed, so the marker's machine never needs the internet.
"""

from pathlib import Path
import sys

import requests

# ---- knobs ----------------------------------------------------------------
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FILE = DATA / "hongkong-air-quality.csv"

# The exact link you downloaded from. On the AQHI download page, right-click the
# CSV link and "Copy link address" -- it ends in .csv and usually carries a date
# or station in the query string.
URL = "PASTE_THE_CSV_LINK_HERE"

# Say who you are. A request with no User-Agent looks like a bot and some
# servers refuse it on principle.
HEADERS = {
    "User-Agent": "SD5913 assignment 2 (airquality-daily-hongkong) — student project",
    "Accept": "text/csv,*/*",
}

TIMEOUT = 60


def main():
    DATA.mkdir(parents=True, exist_ok=True)

    if FILE.exists():
        size = FILE.stat().st_size
        print(f"already here: data/{FILE.name} ({size / 1024:.0f} KB) — not fetching again")
        return

    if "PASTE_THE" in URL:
        sys.exit(
            "URL is still the placeholder.\n"
            "  1. open https://www.aqhi.gov.hk/en/download/past-24-hours-pollutant-concentration.html\n"
            "  2. right-click the CSV download link -> Copy link address\n"
            "  3. paste it into URL at the top of fetch.py\n"
            "If the file was downloaded by hand instead, just copy it into data/ "
            "with this exact name and commit it — the rest of the repo does not care."
        )

    print("asking once:", URL)
    reply = requests.get(URL, headers=HEADERS, timeout=TIMEOUT)
    reply.raise_for_status()

    # Raw bytes, exactly as they arrived. Any cleaning happens later, in airq.py.
    FILE.write_bytes(reply.content)
    print(f"wrote data/{FILE.name} — {len(reply.content) / 1024:.0f} KB")
    print("commit it:  git add data && git commit -m 'Add the raw file'")


if __name__ == "__main__":
    main()
