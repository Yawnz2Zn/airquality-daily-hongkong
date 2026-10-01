# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "plotly", "pandas"]
# ///
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from airq import load_clean

HERE = Path(__file__).resolve().parent
OUT_HTML = HERE / "site" / "index.html"

FIELDS = ["pm25", "pm10", "o3", "no2", "so2", "co"]
LABELS = {
    "pm25": "PM2.5", "pm10": "PM10", "o3": "O3",
    "no2": "NO2", "so2": "SO2", "co": "CO",
}

def to_frame():
    rows = load_clean()
    df = pd.DataFrame([
        {"date": r["date"], **{f: r[f] for f in FIELDS}} for r in rows
    ])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df

def build_panel(df):
    fig = go.Figure()
    for f in FIELDS:
        fig.add_trace(go.Scatter(
            x=df["date"], y=df[f],
            name=LABELS[f],
            mode="lines",
            visible=(f == "pm25"),
            hovertemplate=f"%{{x|%Y-%m-%d}}<br>{LABELS[f]}: %{{y:.1f}}<extra></extra>"
        ))

    # 下拉按钮：全部 / 单独某一种污染物
    vis_all = [True] * len(FIELDS)
    buttons = [dict(label="全部", method="restyle", args=[{"visible": vis_all}])]
    for i, f in enumerate(FIELDS):
        vis = [False] * len(FIELDS)
        vis[i] = True
        buttons.append(dict(label=LABELS[f], method="restyle", args=[{"visible": vis}]))

    fig.update_layout(
        title="香港空气质量交互面板（下拉切换污染物，拖拽时间滑块）",
        xaxis=dict(
            rangeslider_visible=True,
            rangeselector=dict(buttons=[
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(step="all", label="All"),
            ]),
            type="date",
        ),
        updatemenus=[dict(
            buttons=buttons,
            direction="down",
            showactive=True,
            x=1.02, xanchor="left",
            y=1.15, yanchor="top"
        )],
        hovermode="x unified",
        height=600,
    )
    return fig

def main():
    df = to_frame()
    fig = build_panel(df)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUT_HTML, include_plotlyjs=True, full_html=True)
    print("saved:", OUT_HTML)

if __name__ == "__main__":
    main()