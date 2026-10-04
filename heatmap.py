# /// script
# requires-python = ">=3.10"
# dependencies = ["plotly", "numpy"]
# ///
"""Render 2025 as one self-contained animated page.

Writes site/index.html -- open it in a browser, or let GitHub Actions publish it.
No window, no PNG: Python writes the file and stops.

The still version of these same two panels is plot.py.
"""

from pathlib import Path
import json
import math
import re

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from airq import load_clean

# ---- knobs ----------------------------------------------------------------
HERE = Path(__file__).resolve().parent
OUT_HTML = HERE / "site" / "index.html"

TITLE = "A Year of Breathing"
SOURCE = "Hong Kong air-quality open data · EPD"
YEAR = 2025

STEP_MS = 900        # one month per step while playing
HOLD_FRAC = 0.35     # fraction of a step spent resting on the month
GLIDE_MS = 520       # scrub speed when you jump to a month by hand

FIELDS = ["pm25", "pm10", "o3", "no2", "so2", "co"]
LABELS = ["PM2.5", "PM10", "O3", "NO2", "SO2", "CO"]
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

FONT_DISPLAY = ("'Space Grotesk', 'Inter', system-ui, -apple-system, "
                "'Segoe UI', Helvetica, Arial, sans-serif")
FONT_BODY = ("'Inter', system-ui, -apple-system, 'Segoe UI', "
             "Helvetica, Arial, sans-serif")
FONT_MONO = ("'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, "
             "Consolas, monospace")

# PM2.5 ramp: deep night blue -> steel -> teal -> amber -> alarm red
PM_SCALE = [[0.00, "#0a1030"], [0.22, "#1c3b70"], [0.44, "#2f7f9e"],
            [0.64, "#79c08a"], [0.82, "#f2b45c"], [1.00, "#ff5d5d"]]
# six-pollutant ramp (values normalised per pollutant)
MIX_SCALE = [[0.00, "#0d1330"], [0.30, "#3a3f92"], [0.58, "#8a5cf6"],
             [0.80, "#e46ab0"], [1.00, "#ffb37a"]]


# ---- the numbers ----------------------------------------------------------
def calendar_matrix(rows, field):
    """12 x 31 grid of daily values. Days with no reading stay NaN."""
    mat = np.full((12, 31), np.nan)
    for r in rows:
        v = r[field]
        if v is not None:
            mat[r["date"].month - 1, r["date"].day - 1] = v
    return mat


def monthly_matrix(rows):
    """12 x 6 grid of monthly means, raw units."""
    accum = np.zeros((12, len(FIELDS)))
    counts = np.zeros((12, len(FIELDS)))
    for r in rows:
        m = r["date"].month - 1
        for j, f in enumerate(FIELDS):
            if r[f] is not None:
                accum[m, j] += r[f]
                counts[m, j] += 1
    with np.errstate(invalid="ignore"):
        return np.where(counts > 0, accum / np.maximum(counts, 1), np.nan)


def normalise_columns(mat):
    """Six pollutants, six scales. Put each on 0-1 so one colour bar can hold
    them all; the raw value rides along in customdata."""
    out = np.full(mat.shape, np.nan)
    for j in range(mat.shape[1]):
        col = mat[:, j]
        good = col[~np.isnan(col)]
        if good.size == 0:
            continue
        lo, hi = float(good.min()), float(good.max())
        out[:, j] = 0.5 if hi == lo else (col - lo) / (hi - lo)
    return out


def js_list(seq):
    """NaN -> null, two decimals is plenty for a tooltip."""
    return json.dumps([None if v is None or (isinstance(v, float) and math.isnan(v))
                       else round(float(v), 2) for v in seq])


# ---- the page -------------------------------------------------------------
HEAD = """
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
:root{
  --bg:#06070e; --txt:#eaeefb; --dim:#8d95b2; --faint:#5d647e;
  --line:rgba(255,255,255,.09);
}
*{box-sizing:border-box}
html{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
body{
  margin:0;background:var(--bg);color:var(--txt);
  font-family:__BODY__;font-size:15px;line-height:1.55;
  min-height:100vh;overflow-x:hidden;
}
.aq-page{position:relative;max-width:1200px;margin:0 auto;padding:52px 28px 60px}

.aq-aurora{
  position:fixed;inset:-25% -12% auto -12%;height:130%;z-index:-1;pointer-events:none;
  background:
    radial-gradient(680px 420px at 16% 10%, rgba(96,132,255,.22), transparent 62%),
    radial-gradient(600px 380px at 84% 2%,  rgba(255,124,178,.14), transparent 60%),
    radial-gradient(760px 460px at 52% 96%, rgba(110,255,214,.10), transparent 66%);
  filter:blur(8px);animation:aq-drift 28s ease-in-out infinite alternate;
}
@keyframes aq-drift{
  from{transform:translate3d(-2%,-1%,0) scale(1)}
  to  {transform:translate3d(3%,2%,0) scale(1.08)}
}

.aq-eyebrow{
  font-size:11px;font-weight:500;letter-spacing:.22em;text-transform:uppercase;
  color:var(--faint);margin-bottom:14px;
}
.aq-title{
  font-family:__DISPLAY__;font-weight:600;
  font-size:clamp(34px,5.2vw,58px);line-height:1.04;letter-spacing:-.025em;
  margin:0 0 12px;
  background:linear-gradient(96deg,#ffffff 12%, #b9c8ff 52%, #ffb9d8 92%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
.aq-sub{
  max-width:70ch;margin:0;color:var(--dim);font-weight:300;
  font-size:15.5px;letter-spacing:.005em;
}
.aq-head,.aq-stats,.aq-controls,.aq-progress,.aq-panel,.aq-foot{
  opacity:0;animation:aq-rise .8s cubic-bezier(.22,.7,.2,1) forwards;
}
.aq-stats{animation-delay:.10s}.aq-controls{animation-delay:.18s}
.aq-progress{animation-delay:.24s}.aq-panel{animation-delay:.30s}
.aq-foot{animation-delay:.38s}
@keyframes aq-rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}

.aq-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:30px 0 22px}
@media(max-width:760px){.aq-stats{grid-template-columns:repeat(2,1fr)}}
.aq-card{
  padding:14px 16px;border:1px solid var(--line);border-radius:14px;
  background:linear-gradient(180deg,rgba(255,255,255,.055),rgba(255,255,255,.015));
  transition:transform .35s cubic-bezier(.22,.7,.2,1),border-color .35s;
}
.aq-card:hover{transform:translateY(-3px);border-color:rgba(255,255,255,.2)}
.aq-card .k{
  font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--faint);margin-bottom:7px;
}
.aq-card .v{
  font-family:__DISPLAY__;font-size:23px;font-weight:600;letter-spacing:-.01em;
  font-variant-numeric:tabular-nums;
}
.aq-card .v small{font-size:12px;color:var(--dim);font-weight:400;margin-left:3px}

.aq-controls{
  display:flex;align-items:center;gap:20px;flex-wrap:wrap;
  padding:14px 18px;border:1px solid var(--line);border-radius:16px;
  background:rgba(255,255,255,.03);backdrop-filter:blur(10px);
}
.aq-btn{
  display:inline-flex;align-items:center;gap:9px;cursor:pointer;
  padding:10px 20px;border:0;border-radius:999px;
  font-family:__BODY__;font-size:13.5px;font-weight:500;letter-spacing:.02em;
  color:#0a0d1c;background:linear-gradient(96deg,#a9c3ff,#e3c6ff);
  box-shadow:0 6px 22px rgba(140,170,255,.22);
  transition:transform .22s cubic-bezier(.22,.7,.2,1),box-shadow .22s;
}
.aq-btn:hover{transform:translateY(-2px);box-shadow:0 10px 28px rgba(140,170,255,.34)}
.aq-btn:active{transform:translateY(0) scale(.98)}
.aq-ico{font-size:11px;transition:transform .3s}
.aq-btn[data-state="playing"] .aq-ico{transform:rotate(90deg)}

.aq-readout{min-width:210px}
.aq-month{font-family:__DISPLAY__;font-size:17px;font-weight:600;letter-spacing:-.01em}
.aq-readline{display:flex;align-items:baseline;gap:8px;margin-top:2px}
.aq-value{
  font-family:__MONO__;font-size:30px;font-weight:500;line-height:1;
  font-variant-numeric:tabular-nums;letter-spacing:-.02em;
}
.aq-unit{font-size:12px;color:var(--dim)}
.aq-delta{font-family:__MONO__;font-size:11px;padding:2px 7px;border-radius:999px}
.aq-delta.up{color:#ffb37a;background:rgba(255,179,122,.12)}
.aq-delta.down{color:#7ce0b0;background:rgba(124,224,176,.12)}
.aq-cap{font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);margin-top:5px}

.aq-pills{display:flex;gap:5px;flex-wrap:wrap;margin-left:auto}
.pill{
  cursor:pointer;border:1px solid transparent;background:rgba(255,255,255,.05);
  color:var(--dim);border-radius:8px;padding:5px 9px;
  font-family:__MONO__;font-size:11px;letter-spacing:.04em;
  transition:all .28s cubic-bezier(.22,.7,.2,1);
}
.pill:hover{color:var(--txt);background:rgba(255,255,255,.12)}
.pill.on{
  color:#0a0d1c;background:linear-gradient(96deg,#a9c3ff,#e3c6ff);
  font-weight:500;box-shadow:0 4px 14px rgba(140,170,255,.28);
}

.aq-progress{height:2px;background:rgba(255,255,255,.07);border-radius:2px;margin:16px 0 0;overflow:hidden}
.aq-bar{height:100%;width:0;border-radius:2px;background:linear-gradient(90deg,#8fb0ff,#ffb37a);transition:width .08s linear}

.aq-panel{
  position:relative;margin-top:16px;padding:12px 8px 4px;
  border:1px solid var(--line);border-radius:20px;
  background:linear-gradient(180deg,rgba(255,255,255,.055),rgba(255,255,255,.018));
  backdrop-filter:blur(10px);
  height:clamp(440px,58vh,660px);overflow:hidden;
}
.plotly-graph-div{width:100%!important;height:100%!important}

.aq-foot{margin-top:20px;font-size:11.5px;color:var(--faint);letter-spacing:.04em}
.aq-foot code{font-family:__MONO__;color:var(--dim)}
.aq-hint{font-family:__MONO__;font-size:10.5px;color:var(--faint)}
</style>
"""

HERO_OPEN = """
<div class="aq-page">
  <div class="aq-aurora"></div>

  <header class="aq-head">
    <div class="aq-eyebrow">Hong Kong &middot; PM2.5 &middot; __YEAR__</div>
    <h1 class="aq-title">__TITLE__</h1>
    <p class="aq-sub">Every day of __YEAR__ as one tile, scrubbed month by month.
      Left: daily PM2.5 in &micro;g/m&sup3;. Right: six pollutants sharing one
      colour bar, because each has been normalised to its own range &mdash;
      hover any square for the raw number.</p>
  </header>

  <section class="aq-stats">
    <div class="aq-card"><div class="k">Year mean PM2.5</div>
      <div class="v">__ANNUAL__<small>&micro;g/m&sup3;</small></div></div>
    <div class="aq-card"><div class="k">Cleanest month</div>
      <div class="v">__CLEAN__</div></div>
    <div class="aq-card"><div class="k">Peak month</div>
      <div class="v">__PEAK__</div></div>
    <div class="aq-card"><div class="k">Days sampled</div>
      <div class="v">__DAYS__<small>/ __TOTALDAYS__</small></div></div>
  </section>

  <section class="aq-controls">
    <button id="aq-play" class="aq-btn" data-state="paused">
      <span class="aq-ico">&#9654;</span><span id="aq-play-label">Play</span>
    </button>
    <div class="aq-readout">
      <div class="aq-month" id="aq-month">January</div>
      <div class="aq-readline">
        <span class="aq-value" id="aq-value">&mdash;</span>
        <span class="aq-unit">&micro;g/m&sup3;</span>
        <span class="aq-delta" id="aq-delta"></span>
      </div>
      <div class="aq-cap">Monthly mean PM2.5</div>
    </div>
    <div class="aq-pills" id="aq-pills">__PILLS__</div>
  </section>

  <div class="aq-progress"><div class="aq-bar" id="aq-bar"></div></div>

  <section class="aq-panel">
"""

HERO_CLOSE = """
  </section>

  <footer class="aq-foot">
    __SOURCE__ &middot; the raw file lives in <code>data/</code>
    <span class="aq-hint">&nbsp;&nbsp;space = play / pause &nbsp; &larr; &rarr; = step</span>
  </footer>
</div>
"""

JS = """
<script>
(function () {
  var gd = document.getElementById('aq-chart') || document.querySelector('.plotly-graph-div');
  if (!gd) return;

  var MONTHS = __MONTHS__, SHORT = __SHORT__, MEANS = __MEANS__;
  var ANNUAL = __ANNUAL__, N = 12;
  var GLIDE = __GLIDE__, STEP = __STEP__, HOLD = __HOLD__;

  var cur = 0, tgt = 1, dir = 1, shown = 0;
  var playing = false, raf = null, t0 = null;

  var elMonth = document.getElementById('aq-month');
  var elValue = document.getElementById('aq-value');
  var elDelta = document.getElementById('aq-delta');
  var elBar   = document.getElementById('aq-bar');
  var elPlay  = document.getElementById('aq-play');
  var elLabel = document.getElementById('aq-play-label');
  var pills   = [].slice.call(document.querySelectorAll('.pill'));

  function ease(t) { return t < .5 ? 4*t*t*t : 1 - Math.pow(-2*t + 2, 3) / 2; }

  function stepTarget(from, d) {
    var t = from + d;
    if (t > N - 1) { d = -1; t = N - 2; }
    else if (t < 0) { d = 1; t = 1; }
    return [t, d];
  }

  function paint(e) {
    var f  = cur + dir * e;
    var y0 = (N - 1 - f) / N, y1 = (N - f) / N;
    try {
      Plotly.relayout(gd, {'shapes[0].y0': y0, 'shapes[0].y1': y1,
                           'shapes[1].y0': y0, 'shapes[1].y1': y1});
    } catch (err) {}

    var lead = e < .5 ? cur : tgt;
    shown = lead;
    var a = MEANS[cur], b = MEANS[tgt];
    var v = (a === null || b === null) ? null : a + (b - a) * e;

    if (elMonth) elMonth.textContent = MONTHS[lead];
    if (elValue) elValue.textContent = (v === null) ? '\\u2014' : v.toFixed(1);
    if (elDelta) {
      var d = (v === null || ANNUAL === null) ? null : v - ANNUAL;
      elDelta.textContent = (d === null) ? '' :
        (d >= 0 ? '+' : '\\u2212') + Math.abs(d).toFixed(1) + ' vs year';
      elDelta.className = 'aq-delta ' + (d === null ? '' : (d >= 0 ? 'up' : 'down'));
    }
    if (elBar) elBar.style.width = Math.max(0, Math.min(100, f / (N - 1) * 100)) + '%';
    for (var i = 0; i < pills.length; i++) {
      pills[i].classList.toggle('on', i === lead);
    }
  }

  function tick(ts) {
    if (!playing) return;
    if (t0 === null) t0 = ts;
    var el = ts - t0;
    var u = el < HOLD ? 0 : Math.min(1, (el - HOLD) / GLIDE);
    paint(ease(u));
    if (u >= 1) {
      cur = tgt;
      var nx = stepTarget(cur, dir); tgt = nx[0]; dir = nx[1];
      t0 = ts;
    }
    raf = requestAnimationFrame(tick);
  }

  function play() {
    if (playing) return;
    playing = true; t0 = null;
    if (elPlay) elPlay.setAttribute('data-state', 'playing');
    if (elLabel) elLabel.textContent = 'Pause';
    raf = requestAnimationFrame(tick);
  }

  function pause() {
    playing = false;
    if (raf) cancelAnimationFrame(raf);
    if (elPlay) elPlay.setAttribute('data-state', 'paused');
    if (elLabel) elLabel.textContent = 'Play';
  }

  function scrubTo(m) {
    pause();
    if (m === shown) { paint(0); return; }
    cur = shown; tgt = m; dir = m > shown ? 1 : -1;
    var start = null;
    function f(ts) {
      if (start === null) start = ts;
      var u = Math.min(1, (ts - start) / __SCRUB__);
      paint(ease(u));
      if (u < 1) { requestAnimationFrame(f); return; }
      cur = m;
      var nx = stepTarget(cur, dir); tgt = nx[0]; dir = nx[1];
      paint(0);
    }
    requestAnimationFrame(f);
  }

  pills.forEach(function (p, i) {
    p.addEventListener('click', function () { scrubTo(i); });
  });
  if (elPlay) elPlay.addEventListener('click', function () {
    playing ? pause() : play();
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.code === 'Space') { ev.preventDefault(); playing ? pause() : play(); }
    else if (ev.key === 'ArrowRight') scrubTo(Math.min(N - 1, shown + 1));
    else if (ev.key === 'ArrowLeft')  scrubTo(Math.max(0, shown - 1));
  });

  paint(0);
})();
</script>
"""


def main():
    rows = load_clean()
    cal = calendar_matrix(rows, "pm25")
    mon = monthly_matrix(rows)
    mix = normalise_columns(mon)

    with np.errstate(invalid="ignore"):
        means = [float(np.nanmean(cal[m])) if np.any(~np.isnan(cal[m])) else np.nan
                 for m in range(12)]
    valid = cal[~np.isnan(cal)]
    annual = float(np.nanmean(valid)) if valid.size else float("nan")

    ok = [m for m in range(12) if not math.isnan(means[m])]
    clean_i = min(ok, key=lambda m: means[m]) if ok else None
    peak_i = max(ok, key=lambda m: means[m]) if ok else None

    zmin = float(np.nanmin(valid)) if valid.size else 0.0
    zmax = float(np.nanmax(valid)) if valid.size else 1.0

    # ---- traces -----------------------------------------------------------
    left = go.Heatmap(
        z=cal, x=list(range(1, 32)), y=SHORT,
        colorscale=PM_SCALE, zmin=zmin, zmax=zmax,
        xgap=2, ygap=2,
        hovertemplate="%{y} %{x} · %{z:.1f} µg/m³<extra></extra>",
        colorbar=dict(title=dict(text="PM2.5 µg/m³",
                                 font=dict(family=FONT_BODY, size=11)),
                      thickness=11, len=.82, outlinewidth=0,
                      tickfont=dict(family=FONT_MONO, size=10)),
    )
    right = go.Heatmap(
        z=mix, x=LABELS, y=SHORT,
        customdata=mon,
        colorscale=MIX_SCALE, zmin=0, zmax=1,
        xgap=2, ygap=2,
        hovertemplate="%{y} · %{x}: %{customdata:.1f}<extra></extra>",
        colorbar=dict(title=dict(text="relative level",
                                 font=dict(family=FONT_BODY, size=11)),
                      thickness=11, len=.82, outlinewidth=0,
                      tickfont=dict(family=FONT_MONO, size=10)),
    )

    band = dict(type="rect", xref="x domain", yref="y domain",
                x0=0, x1=1, y0=11 / 12, y1=1,
                fillcolor="rgba(255,255,255,.07)",
                line=dict(color="rgba(255,255,255,.85)", width=1.4), layer="above")
    band2 = dict(band, xref="x2 domain", yref="y2 domain")

    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.13,
                        subplot_titles=("PM2.5 · every day of the year",
                                        "Six pollutants · monthly means"))
    fig.add_trace(left, row=1, col=1)
    fig.add_trace(right, row=1, col=2)

    fig.update_layout(
        shapes=[band, band2],
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_BODY, size=12.5, color="#aeb6d0"),
        margin=dict(l=58, r=24, t=54, b=54),
        hoverlabel=dict(font_family=FONT_MONO, font_size=12,
                        bgcolor="#111527", bordercolor="#2a3350"),
        height=620,
    )
    for ann in fig.layout.annotations:
        ann.font.update(family=FONT_DISPLAY, size=13.5, color="#e9edfb")

    fig.update_xaxes(title_text="day of month", row=1, col=1,
                     tickfont=dict(family=FONT_MONO, size=10),
                     title_font=dict(family=FONT_BODY, size=11),
                     dtick=5, gridwidth=0, zeroline=False)
    fig.update_yaxes(row=1, col=1, tickfont=dict(family=FONT_MONO, size=10),
                     gridwidth=0, autorange="reversed")
    fig.update_xaxes(row=1, col=2, tickfont=dict(family=FONT_MONO, size=10),
                     gridwidth=0, zeroline=False)
    fig.update_yaxes(row=1, col=2, tickfont=dict(family=FONT_MONO, size=10),
                     gridwidth=0, autorange="reversed")

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUT_HTML, include_plotlyjs=True, full_html=True,
                   div_id="aq-chart", default_width="100%", default_height="100%",
                   config={"displayModeBar": False, "responsive": True})

    # ---- dress the page up ------------------------------------------------
    def fmt(v, nd=1):
        return "—" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.{nd}f}"

    pills = "".join(f'<button class="pill" data-m="{i}">{s}</button>'
                    for i, s in enumerate(SHORT))

    head = (HEAD.replace("__DISPLAY__", FONT_DISPLAY)
                .replace("__BODY__", FONT_BODY)
                .replace("__MONO__", FONT_MONO))

    hero = (HERO_OPEN.replace("__YEAR__", str(YEAR))
                     .replace("__TITLE__", TITLE)
                     .replace("__ANNUAL__", fmt(annual))
                     .replace("__CLEAN__", SHORT[clean_i] if clean_i is not None else "—")
                     .replace("__PEAK__", SHORT[peak_i] if peak_i is not None else "—")
                     .replace("__DAYS__", str(int(valid.size)))
                     .replace("__TOTALDAYS__", "365")
                     .replace("__PILLS__", pills))

    close = HERO_CLOSE.replace("__SOURCE__", SOURCE)

    js = (JS.replace("__MONTHS__", json.dumps(MONTHS))
            .replace("__SHORT__", json.dumps(SHORT))
            .replace("__MEANS__", js_list(means))
            .replace("__ANNUAL__", "null" if math.isnan(annual) else repr(round(annual, 2)))
            .replace("__GLIDE__", str(int(STEP_MS * (1 - HOLD_FRAC))))
            .replace("__STEP__", str(int(STEP_MS)))
            .replace("__HOLD__", str(int(STEP_MS * HOLD_FRAC)))
            .replace("__SCRUB__", str(int(GLIDE_MS))))

    html = OUT_HTML.read_text(encoding="utf-8")
    if "<head>" in html:
        html = re.sub(r"<head>", lambda m: m.group(0) + head, html, count=1)
    else:
        html = head + html
    html = re.sub(r"<body[^>]*>", lambda m: m.group(0) + hero, html, count=1)
    html = re.sub(r"</body>", lambda m: js + close + m.group(0), html, count=1)
    OUT_HTML.write_text(html, encoding="utf-8")

    print("saved:", OUT_HTML, f"({OUT_HTML.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
