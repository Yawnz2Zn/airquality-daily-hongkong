# airquality-daily-hongkong

Every day of 2025 as one tile — twelve months down, thirty-one days across,
coloured by how much PM2.5 was in the air.

![PM2.5 calendar, Hong Kong, 2025](out/plot.png)

**[Interactive version](https://Yawnz2ZN.github.io/airquality-daily-hongkong/)**
— scrub the months, hover a square for the raw number.
# The phenomenon

![what the picture is](out/plot.png)

## The phenomenon
Fine particulate matter under 2.5 micrometres: small enough to hang in the air for
days and to reach the lungs, and invisible when it is bad. It is not spread evenly
over the year — it rides the monsoon. Winter brings continental air down from the
north and the level climbs; summer brings rain, which washes it out.

## The source

Hong Kong Environmental Protection Department, hourly pollutant concentrations:
<https://www.aqhi.gov.hk/en/download/past-24-hours-pollutant-concentration.html>

`fetch.py` asks once and writes the reply to `data/hongkong-air-quality.csv`
exactly as it arrived — unchanged, committed, no key, no login. The file holds
4,645 rows covering 2014 to 2026; `airq.py` takes the 2025 slice and parses it to
one row per day. It prints the first row, one value and that value's `type()`
before anything is drawn — the CSV arrives as text, and a plot built from strings
is empty and silent.
## What the picture shows

Winter sits at the top and bottom of the grid, summer in the middle. December is
the dirtiest month at 48 µg/m³, September the cleanest at 21. Six pollutants share
the right-hand panel as monthly means.

**What it hides.** Each tile is a daily *mean*, so a rush-hour spike and a calm
afternoon average to the same square — the peak is gone. Three days at the end of
December have no reading and show up as blank cells. The year is one file's year,
which discards the wide gap between roadside and background stations. And the six
pollutants live on different scales, so each is normalised to its own range: the
colour bar reads *relative level*, and absolute values survive only in the hover
text of the interactive version.
## Run it

```
uv run fetch.py     # writes data/ — skipped if it is already there
uv run airq.py      # parses, prints one row, one value, its type
uv run plot.py      # writes out/plot.png
uv run animate.py   # writes site/index.html — open it in a browser
```
