# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Draw 2025 as a calendar: 12 months down, 31 days across, one tile per day.

Writes out/plot.png -- the picture the README shows. The interactive version of
the same numbers is animate.py.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch
from matplotlib import gridspec

from airq import load_clean

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
PNG = OUT / "plot.png"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
POLLUTANTS = ["pm25", "pm10", "o3", "no2", "so2", "co"]
LABELS = ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"]

BACKGROUND = "#0b0e1a"
PANEL = "#12162a"
EMPTY = "#1b2038"
TEXT = "#eef1fb"
DIM = "#8d95b2"
FAINT = "#5d647e"

# The two ramps must match animate.py, or the PNG and the page disagree.
# Left, PM2.5: deep blue -> steel -> teal -> amber -> red
PM_RAMP = [(0.00, "#0a1030"), (0.22, "#1c3b70"), (0.44, "#2f7f9e"),
           (0.64, "#79c08a"), (0.82, "#f2b45c"), (1.00, "#ff5d5d")]
# Right, six pollutants normalised: indigo -> violet -> magenta -> peach
MIX_RAMP = [(0.00, "#0d1330"), (0.30, "#3a3f92"), (0.58, "#8a5cf6"),
            (0.80, "#e46ab0"), (1.00, "#ffb37a")]
ACCENT = ["#a9c3ff", "#e3c6ff", "#ffb37a"]

# Pick the first font that exists on this machine. Segoe UI on Windows,
# Helvetica on macOS, DejaVu Sans anywhere matplotlib is installed.
_AVAILABLE = {f.name for f in fm.fontManager.ttflist}
FONT = next((n for n in ("Segoe UI", "Helvetica Neue", "DejaVu Sans")
             if n in _AVAILABLE), "DejaVu Sans")
MONO = next((n for n in ("Consolas", "JetBrains Mono", "DejaVu Sans Mono")
             if n in _AVAILABLE), "DejaVu Sans Mono")


def calendar(rows):
    """12 x 31 of daily PM2.5. Days with no reading stay NaN."""
    grid = np.full((12, 31), np.nan)
    for r in rows:
        grid[r["date"].month - 1, r["date"].day - 1] = r["pm25"]
    return grid


def monthly(rows):
    """12 x 6 of monthly MEANS, each pollutant normalised to its own range.

    The old version did `grid[m, j] = r[f]` inside the loop, which overwrote
    every day with the next one and left the last day of the month standing in
    for the mean. Accumulate and divide instead.
    """
    accum = np.zeros((12, 6))
    counts = np.zeros((12, 6))
    for r in rows:
        m = r["date"].month - 1
        for j, f in enumerate(POLLUTANTS):
            if r[f] is not None:
                accum[m, j] += r[f]
                counts[m, j] += 1
    with np.errstate(invalid="ignore"):
        grid = np.where(counts > 0, accum / np.maximum(counts, 1), np.nan)
    for j in range(6):
        col = grid[:, j]
        good = col[~np.isnan(col)]
        if good.size:
            lo, hi = good.min(), good.max()
            grid[:, j] = 0.5 if hi == lo else (col - lo) / (hi - lo)
    return grid


def heat(ax, grid, title, xlabel, xticks, xlabels, cbar, ramp, lo=None, hi=None):
    stops = [s for s, _ in ramp]
    span = stops[-1] - stops[0]
    cmap = LinearSegmentedColormap.from_list(
        "aq", [((s - stops[0]) / span, c) for s, c in ramp], N=256)
    cmap.set_bad(EMPTY)
    vmin = np.nanmin(grid) if lo is None else lo
    vmax = np.nanmax(grid) if hi is None else hi
    im = ax.imshow(np.ma.masked_invalid(grid), aspect="auto", cmap=cmap,
                   vmin=vmin, vmax=vmax)
    ax.set_title(title, fontsize=12, color=TEXT, font=FONT,
                 fontweight="bold", pad=11, loc="left")
    ax.set_xlabel(xlabel, fontsize=9.5, color=FAINT, labelpad=6)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels, fontsize=9, color=DIM, font=MONO)
    ax.set_yticks(range(12))
    ax.set_yticklabels(MONTHS, fontsize=9, color=DIM, font=MONO)
    ax.tick_params(length=0, pad=5)
    for side in ax.spines.values():
        side.set_visible(False)
    cb = ax.figure.colorbar(im, ax=ax, fraction=0.032, pad=0.035)
    cb.outline.set_visible(False)
    cb.set_label(cbar, fontsize=8.5, color=FAINT, labelpad=7)
    cb.ax.tick_params(labelsize=8.5, length=0, colors=DIM)
    for t in cb.ax.get_yticklabels():
        t.set_fontfamily(MONO)


def card(ax, x, y, w, h, label, value, unit=""):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, transform=ax.transAxes,
        boxstyle="round,pad=0,rounding_size=0.045",
        linewidth=1, edgecolor="#252c4a", facecolor=PANEL))
    # manual letter-spacing: matplotlib has no letterspacing kwarg on every
    # version, so space the label out by hand
    ax.text(x + 0.045, y + h * 0.66, " ".join(label.upper()),
            transform=ax.transAxes, fontsize=6.8, color=FAINT,
            font=FONT, fontweight="bold", va="center")
    ax.text(x + 0.045, y + h * 0.27, value, transform=ax.transAxes,
            fontsize=15, color=TEXT, font=FONT, fontweight="bold", va="center")
    if unit:
        ax.text(x + 0.045 + len(value) * 0.034, y + h * 0.24, unit,
                transform=ax.transAxes, fontsize=8, color=DIM, va="center")


def main():
    rows = load_clean()
    cal = calendar(rows)
    means = [np.nanmean(cal[m]) if np.any(~np.isnan(cal[m])) else np.nan
             for m in range(12)]

    print("first row:", rows[0])
    print("one value:", rows[0]["pm25"], type(rows[0]["pm25"]).__name__)
    print("days:", len(rows), "  year mean PM2.5: %.1f" % np.nanmean(cal))

    annual = float(np.nanmean(cal))
    ok = [m for m in range(12) if not np.isnan(means[m])]
    clean_i = min(ok, key=lambda m: means[m])
    peak_i = max(ok, key=lambda m: means[m])

    OUT.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(14, 7.4), facecolor=BACKGROUND)
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.5, 3.4], width_ratios=[2.6, 1],
                           hspace=0.30, wspace=0.26,
                           left=0.038, right=0.985, top=0.94, bottom=0.07)

    # ---- header -----------------------------------------------------------
    head = fig.add_subplot(gs[0, :])
    head.set_axis_off()
    head.text(0, 0.86, "Air quality, day by day", fontsize=25, color=TEXT,
              font=FONT, fontweight="bold", va="center", transform=head.transAxes)
    head.text(0.238, 0.855, "Hong Kong · 2025", fontsize=25, color=ACCENT[0],
              font=FONT, fontweight="bold", va="center", transform=head.transAxes)
    head.text(0, 0.56,
              "Every day of the year as one tile, coloured by PM2.5 in µg/m³. "
              "Winter sits at the top and bottom, summer in the middle.",
              fontsize=10.5, color=DIM, va="center", transform=head.transAxes)

    w, gap = 0.238, 0.016
    cards = [("Year mean PM2.5", f"{annual:.1f}", "µg/m³"),
             ("Cleanest month", f"{MONTHS[clean_i]}  {means[clean_i]:.0f}", ""),
             ("Peak month", f"{MONTHS[peak_i]}  {means[peak_i]:.0f}", ""),
             ("Days sampled", f"{int(np.count_nonzero(~np.isnan(cal)))}", "/ 365")]
    for i, (k, v, u) in enumerate(cards):
        card(head, i * (w + gap), 0.0, w, 0.34, k, v, u)

    # ---- panels -----------------------------------------------------------
    # The colour range is shared with animate.py: the day grid spans the lowest
    # and highest single day, the pollutant panel is always 0 to 1.
    lo, hi = float(np.nanmin(cal)), float(np.nanmax(cal))
    heat(fig.add_subplot(gs[1, 0]), cal,
         "PM2.5 · one tile per day", "day of month",
         range(0, 31, 5), range(1, 32, 5), "PM2.5 µg/m³", PM_RAMP, lo, hi)
    heat(fig.add_subplot(gs[1, 1]), monthly(rows),
         "Six pollutants · monthly means", "pollutant",
         range(6), LABELS, "relative level", MIX_RAMP, 0, 1)

    fig.text(0.038, 0.028,
             "Each pollutant is scaled to its own range, so the colour bar "
             "reads relative level.  Source: Hong Kong EPD.",
             fontsize=8, color=FAINT)

    fig.savefig(PNG, dpi=170, facecolor=BACKGROUND)
    print("wrote out/plot.png")
    plt.show()


if __name__ == "__main__":
    main()
