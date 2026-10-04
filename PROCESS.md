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

## Rejected
