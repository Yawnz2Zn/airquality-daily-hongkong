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

def traces_for_months(monthly, months_so_far):
    vmax = float(np.nanmax(monthly))

    xs, ys, vals = [], [], []
    for m in range(1, months_so_far + 1):
        for j, lab in enumerate(LABELS):
            v = monthly[m - 1, j]
            if v is not None and not np.isnan(v):
                xs.append(m)
                ys.append(lab)
                vals.append(v)

    sizes = [10 + 35 * (v / vmax) for v in vals]

    base = dict(
        x=xs, y=ys,
        mode="markers",
        text=[f"{v:.1f}" for v in vals],
        hovertemplate="%{y} · %{x}月<br>浓度: %{text} µg/m³<extra></extra>",
    )

    halo = go.Scatter(
        **base,
        marker=dict(
            size=[s * 3 for s in sizes],
            color=vals,
            colorscale="plasma",
            cmin=0, cmax=vmax,
            opacity=0.18,
            line=dict(width=0),
        ),
        hoverinfo="skip",
        showlegend=False,
    )

    core = go.Scatter(
        **base,
        marker=dict(
            size=sizes,
            color=vals,
            colorscale="plasma",
            cmin=0, cmax=vmax,
            opacity=0.95,
            line=dict(width=0),
            colorbar=dict(title="浓度"),
        ),
        showlegend=False,
    )

    return [halo, core]

def main():
    rows = load_clean()
    monthly = monthly_matrix(rows)

    fig = go.Figure(
        data=traces_for_months(monthly, 1),
        frames=[
            go.Frame(
                name=MONTHS[m - 1],
                data=traces_for_months(monthly, m),
            )
            for m in range(2, 13)
        ],
    )

    y_cats = LABELS
    fig.update_yaxes(categoryorder="array", categoryarray=y_cats)

    sliders_steps = []
    for i, month in enumerate(MONTHS, start=1):
        sliders_steps.append(dict(
            label=month,
            method="animate",
            args=[[month], dict(frame=dict(duration=500, redraw=True),
                                mode="immediate")]
        ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgb(5,5,10)",
        plot_bgcolor="rgb(5,5,10)",
        title=dict(
            text="香港空气质量 · 星空气泡矩阵",
            font=dict(size=22, color="white"),
            x=0.5,
        ),
        xaxis=dict(
            title="月份",
            range=[1, 12],
            dtick=1,
            gridcolor="rgba(255,255,255,0.08)",
        ),
        yaxis=dict(
            title="污染物",
            gridcolor="rgba(255,255,255,0.08)",
        ),
        height=650,
        hovermode="closest",
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            x=0.01,
            y=1.12,
            buttons=[
                dict(
                    label="▶ 播放月份",
                    method="animate",
                    args=[None, dict(frame=dict(duration=700, redraw=True),
                                     fromcurrent=True, mode="immediate")],
                ),
                dict(
                    label="⏸ 暂停",
                    method="animate",
                    args=[None, dict(frame=dict(duration=0, redraw=False),
                                     mode="immediate")],
                ),
            ],
        )],
        sliders=[dict(
            active=0,
            currentvalue=dict(prefix="月份: "),
            pad=dict(t=50),
            steps=sliders_steps,
        )],
    )

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUT_HTML, include_plotlyjs=True, full_html=True)
    print("saved:", OUT_HTML)

if __name__ == "__main__":
    main()