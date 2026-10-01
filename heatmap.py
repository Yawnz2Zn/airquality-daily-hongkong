# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "plotly", "pandas"]
# ///
from pathlib import Path
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from airq import load_clean

HERE = Path(__file__).resolve().parent
OUT_HTML = HERE / "site" / "index.html"

FIELDS = ["pm25", "pm10", "o3", "no2", "so2", "co"]
LABELS = ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"]
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
          "Jul","Aug","Sep","Oct","Nov","Dec"]

def month_daily_values(rows, field, month):
    days = np.full(31, np.nan)
    counts = np.zeros(31)
    for r in rows:
        if r["date"].month == month:
            d = r["date"].day - 1
            v = r[field]
            if v is not None and not np.isnan(v):
                if counts[d] == 0:
                    days[d] = v
                else:
                    days[d] = (days[d] * counts[d] + v) / (counts[d] + 1)
                counts[d] += 1
    return days

def calendar_matrix(rows, field):
    mat = np.full((12, 31), np.nan)
    counts = np.zeros((12, 31))
    for r in rows:
        m, d = r["date"].month - 1, r["date"].day - 1
        v = r[field]
        if v is not None and not np.isnan(v):
            if counts[m, d] == 0:
                mat[m, d] = v
            else:
                mat[m, d] = (mat[m, d] * counts[m, d] + v) / (counts[m, d] + 1)
            counts[m, d] += 1
    return mat

def monthly_matrix(rows):
    accum = np.zeros((12, len(FIELDS)))
    counts = np.zeros((12, len(FIELDS)))
    for r in rows:
        m = r["date"].month - 1
        for j, f in enumerate(FIELDS):
            v = r[f]
            if v is not None and not np.isnan(v):
                accum[m, j] += v
                counts[m, j] += 1
    with np.errstate(invalid="ignore"):
        return np.where(counts > 0, accum / np.maximum(counts, 1), np.nan)

def main():
    rows = load_clean()
    cal = calendar_matrix(rows, "pm25")
    mon = monthly_matrix(rows)

    pm25_all = cal[~np.isnan(cal)]
    zmin = float(np.nanmin(pm25_all)) if len(pm25_all) else 0
    zmax = float(np.nanmax(pm25_all)) if len(pm25_all) else 1

    jan = month_daily_values(rows, "pm25", 1)
    left_initial = go.Heatmap(
        z=[jan],
        x=list(range(1, 32)),
        y=["Jan"],
        colorscale="Viridis",
        zmin=zmin, zmax=zmax,
        hovertemplate="1月 %{x}日: %{z:.1f} µg/m³<extra></extra>",
        colorbar=dict(title="PM2.5"),
    )

    right = go.Heatmap(
        z=mon,
        x=LABELS,
        y=MONTHS,
        colorscale="Plasma",
        hovertemplate="%{y} · %{x}: %{z:.1f}<extra></extra>",
        colorbar=dict(title="月均浓度"),
    )

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("PM2.5 日值 · 随月份播放", "六污染物逐月均值"),
        horizontal_spacing=0.14,
    )
    fig.add_trace(left_initial, row=1, col=1)
    fig.add_trace(right, row=1, col=2)

    frames = []
    for i, month in enumerate(MONTHS, start=1):
        daily = month_daily_values(rows, "pm25", i)
        frame_left = go.Heatmap(
            z=[daily],
            x=list(range(1, 32)),
            y=[month],
            colorscale="Viridis",
            zmin=zmin, zmax=zmax,
            hovertemplate=f"{month} %{{x}}日: %{{z:.1f}} µg/m³<extra></extra>",
            colorbar=dict(title="PM2.5"),
        )
        frames.append(go.Frame(
            name=month,
            data=[frame_left, right],
            layout=dict(title=f"香港空气质量 · {month}")
        ))

    fig.frames = frames

    fig.update_layout(
        template="plotly_dark",
        height=600,
        showlegend=False,
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            x=0.01, y=1.15,
            buttons=[
                dict(
                    label="▶ 播放月份",
                    method="animate",
                    args=[None, dict(frame=dict(duration=600, redraw=True),
                                     fromcurrent=True, mode="immediate")]
                ),
                dict(
                    label="⏸ 暂停",
                    method="animate",
                    args=[None, dict(frame=dict(duration=0, redraw=False),
                                     mode="immediate")]
                )
            ]
        )],
        sliders=[dict(
            active=0,
            currentvalue=dict(prefix="月份: "),
            pad=dict(t=40),
            steps=[
                dict(label=MONTHS[i], method="animate",
                     args=[[MONTHS[i]], dict(frame=dict(duration=0, redraw=True),
                                            mode="immediate")])
                for i in range(12)
            ]
        )]
    )

    fig.update_xaxes(title_text="日", row=1, col=1)
    fig.update_yaxes(title_text="月", row=1, col=1)
    fig.update_xaxes(title_text="污染物", row=1, col=2)
    fig.update_yaxes(title_text="月", row=1, col=2)

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUT_HTML, include_plotlyjs=True, full_html=True)
    print("saved:", OUT_HTML)

if __name__ == "__main__":
    main()