# Process

<!-- Same as assignment 1, same honesty. Which tools you used and for what; one
thing you kept and why it was good; one thing you rejected and why it was wrong.
"I did not use any" is fine if it is true.

If a model wrote most of plot.py, which is likely and allowed, the interesting part
is what you had to correct: did it invent a column name, use pandas where a list
would do, silently drop the rows it could not parse? -->

## Tools
- `uv run` for every command, so each script carries its own `# /// script`
  dependency block and nothing was installed by hand.
- Python, `numpy`, `matplotlib` (the PNG) and `plotly` (the web page).
- An AI coding assistant (DeepSeek) for the **implementation**.

**What was mine, and what was the assistant's.** The phenomenon, the question the
picture answers, the shape of the chart, the colour ramp, what goes on which axis
and what gets left out — all decided before any code was written. I printed the
numbers first and I already knew I wanted a calendar: one tile per real day,
twelve months down, thirty-one days across, dark, with the six pollutants
normalised or the panel would be useless.

The assistant did the part I could not do by hand: the CSS, the animation loop,
the easing, the font stack, the matplotlib boilerplate. I described it, it wrote
it, I ran it, I looked at it, and I sent it back when it was wrong.

Three errors worth writing down. In each case **the code ran cleanly and drew a
picture that was wrong**, so none of them were crashes — I caught them by deciding
in advance what the numbers had to look like and refusing to accept a picture
that disagreed.

- It trusted the file's header. The published file labels `pm25` and `pm10` the
  wrong way round. The first parse reported 362 clean days, silently. I asked for
  a check that PM2.5 can never exceed PM10 — it is a subset — and 360 of 362 days
  turned out to be impossible.
- It wrote `grid[m, j] = r[f]` inside the daily loop of `monthly()`. Each day
  overwrote the last, so the "monthly mean" was the final day of the month. I
  found it because the PNG and the page disagreed on colour.
- It built a 12 × 31 grid over the whole file without asking how many years it
  held. Thirteen. Every tile was the mean of thirteen dates that merely shared a
  month and a day — a plausible picture of something that does not exist.
## Kept

**The calendar.** I first drew the year as a single row of 31 tiles; a row can
only ever show one month, so the shape of the year was invisible. The grid shows
it at once — winter at the top and bottom, summer in the middle.

**The six-pollutant panel**, normalised per pollutant. On one linear scale CO sat
near 0.5 and PM10 near 40, so CO came out a solid black column.

**One year only.** Pooling all thirteen years into one grid threw away the fact
that Hong Kong's PM2.5 fell from about 160 µg/m³ in 2014 to about 31 in 2025.
One real day per tile beats a decade averaged into a blur.

## Rejected

**Plotly's own animation frames** — its play button redraws the whole figure per
step, so the crossing was a hard jump and the colour bar flickered. I wanted it
to move, not step: a JavaScript loop now interpolates the mean and slides the
highlight band with easing.

**A screenshot as the still picture** — that is a photograph of a web page, and
it cannot be reproduced on the marker's machine. `plot.py` redraws both panels in
matplotlib instead; making the two agree is what exposed the `monthly()` bug.

**Pretending the file was clean.** Nine rows have no PM2.5 and three December
days are missing. They are drawn empty, not filled in with a guess.
