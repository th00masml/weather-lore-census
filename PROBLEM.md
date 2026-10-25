# Did the weather proverbs know anything? A corpus-scale census

## The original statement

Richard Inwards, *Weather Lore: A Collection of Proverbs, Sayings, and
Rules Concerning the Weather* (London: Elliot Stock, 3rd ed. 1898; 1st ed.
1869). Inwards assembled thousands of weather proverbs and stated the
unmet task in his Introduction: the sayings are printed so that

> "the reader may judge for himself" their worth — collected "from all
> quarters", their truth "must be left to the test of experience."

That test was never run. The book is a corpus of untested forecasting
claims ("If Candlemas Day be fine and clear, / Corn and fruits will then
be dear"), each implicitly a conditional prediction about later weather.

Source scan (public domain): Internet Archive,
https://archive.org/details/weatherlorecolle00inwa (pub. 1898; Inwards
d. 1937 — US public domain by pre-1929 publication). See DATA-LICENSES.md.

## The bound and the capability

Labor, twice over. First: formalising thousands of archaic verse-proverbs
into precise testable rules is philological hand-work nobody has done at
scale. Second: evaluating each rule needs long homogeneous daily weather
series and statistics that did not exist in 1898. The LLM's role is the
first half only: **translating archaic prose into machine-testable rules**
(condition window/variable/direction → predicted window/variable/
direction). It is a parser, not a judge. A deterministic evaluator then
tests every rule against 253 years of daily English temperature and 94
years of daily England-Wales precipitation. The verdict on each proverb
comes from the sky, not from the model.

## Still open

The state of the art is spot-checks: individual proverbs ("red sky at
night", Groundhog Day) and, most recently, exactly TWO Hebrew rain
proverbs tested against Israeli station data (arXiv 2605.10960, 2026). No
corpus-scale census of a historic weather-lore collection exists.

## Data

- Proverbs: Inwards 1898 (public domain), "Times and Seasons" chapter
  (calendar-anchored sayings).
- Temperature: HadCET daily mean Central England Temperature, 1772-2025,
  Met Office Hadley Centre, Open Government Licence (attribution).
- Precipitation: HadEWP daily England & Wales precipitation, 1931-2025,
  Met Office Hadley Centre, Open Government Licence.

## Design (fixed before any model call)

Extraction (the instrument): `claude-sonnet-5` reads the chapter in
chunks and emits, per proverb, JSON: quote, condition {day-of-year window,
variable in {temp, precip}, direction in {above, below}}, outcome {later
window, variable, direction}, testable flag. Untestable sayings (sky
colour, animals, wind — no matching variable) are marked and skipped.
Rules deduplicated on (condition, outcome).

Evaluation (deterministic, no model): for each year, a window's value =
mean CET anomaly vs day-of-year climatology (temp) or total precipitation
(precip); direction judged against the median across years, so base rates
are ~0.5. Rule skill = P(outcome | condition) - P(outcome | not
condition). Significance: 1000 permutations of outcome years (seed 0);
Benjamini-Hochberg FDR over all rules at q < 0.10.

## Primary metric and kill criterion (fixed now)

The measurable claim is about the instrument: can the LLM formalise the
lore at scale, faithfully?

- **Yield**: >= 50 distinct evaluable rules extracted from the chapter.
- **Fidelity**: on a random audit of 25 extracted rules (seed 0), >= 80%
  faithfully render the proverb's meaning (window, variable, directions),
  judged by reading each pair and recorded in RESULTS.md.

**Kill criterion:** yield < 50 or fidelity < 0.80 → KILLED-AT-4 (the
instrument cannot formalise the corpus reliably). No threshold moves.

The **census result** — how many proverbs show real skill vs the expected
false-discovery count — is the scientific readout, and it is honest in
either direction: "Victorian weather lore has (mostly) no skill" is as
publishable as the opposite. It is preregistered that ALL evaluable rules
are reported, with effect sizes and FDR-corrected significance; no
post-hoc selection.

## Memorization

Structurally irrelevant to the census: the model never predicts weather
and never sees the weather data; every verdict is computed from HadCET/
HadEWP by a deterministic evaluator. The only model output is the
formalisation, whose quality is audited directly (fidelity check). A
model's prior beliefs about which proverbs are true cannot change what
the 253-year record says.
