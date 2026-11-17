# Results — the Weather Lore Census

Run date: 2026-08-10 (extraction); evaluation corrected and extended
2026-11. Extraction model: `claude-sonnet-5` (authenticated CLI, no API
key), used ONLY as a parser. Evaluation: deterministic, no model.
Everything recomputes from cached `outputs/`.

## Verdict (revised 2026-11)

The instrument works: both preregistered gates passed (below). The census
result needs a narrower reading than the August write-up gave it.

- **Two evaluator bugs were found and fixed** (details below). Corrected,
  **10 of 76 rules** are FDR-significant (was 11).
- **Every significant rule is persistence restated.** All ten use the same
  variable on both sides, so the proverb's condition *is* the trivial
  "the anomaly carries on" predictor; their skill equals its skill
  exactly. None of the 15 rules that predict one variable from another
  adds skill beyond persistence after FDR.
- **The folk calendar picked no better dates than chance.** Against 200
  random rules per proverb with the same variables, window lengths and
  lag (detrended), the proverbs' mean |skill| is 0.099 against 0.097, and
  2 of 76 rules beat the random 95th percentile where 3.8 are expected.
- Removing the CET warming trend (31-year running mean) leaves **7**
  significant rules; the secular trend inflated three.

So: proverbs that say "cold now, cold for a while" are true because
English weather persists; proverbs that promise a reversal are refuted with
the opposite sign for the same reason; long-range seasonal prophecies show
no skill. That is a census of what the lore encodes, not evidence that
Victorian observers knew anything a persistence forecast does not.

## Gate 1 — Yield (preregistered: >= 50)

92 raw rules extracted from the "Times and Seasons" chapter (75 chunks);
**76 distinct valid rules** after validation and dedup, all 76 evaluable
(none lost to insufficient data). PASS.

## Gate 2 — Fidelity (preregistered: >= 0.80 on a 25-rule audit)

Random sample of 25 rule/proverb pairs (seed 0, `outputs/audit_sample.json`),
each judged by reading quote against formalisation: **23/25 strictly
faithful (0.92)**; the two debatable cases ("misty + hoar-frost morning"
and "sunbeam on Bridget's day -> snow before May") use the preregistered
coarse mappings (frost/snow -> temp-below, clear -> precip-below) and were
counted as loose, not wrong. PASS.

## Corrections to the evaluator (2026-11)

Found while building the persistence baseline, whose independent
array-based evaluator disagreed with `census.json` by up to 0.20 in skill.

1. **Windows crossing New Year ran for a whole year.** `window_days`
   stopped when the stepped date equalled the end date, which never happens
   for a window such as Dec 1 – Feb 28 (the end lies in the reference year,
   the stepped date runs into the next). Such windows silently became
   367-day windows. Fixed by comparing month and day.
2. **Outcomes earlier in the calendar than the condition were read from the
   same year**, i.e. before the condition ("no snow before January, more in
   March and April" was tested against the preceding March). 14 of 76
   rules. Fixed: the outcome is read from the following year.

After the fix the independent evaluator in `src/baselines.py` reproduces
every census skill to within 5e-5. `tests/test_evaluate.py` pins both
fixes. The August numbers (11 significant, sensitivity 9) are superseded.

## Population: 92 -> 76

92 rules were extracted; all 92 pass validation, none has an identical
condition and outcome, and 16 are duplicates of another rule on
(condition, outcome). The FDR family is the 76 distinct rules.

## The census (primary analysis as preregistered, evaluator corrected)

76 rules, each tested on up to 254 years of daily Central England
Temperature (1772-2025) and 95 years of daily England-Wales precipitation
(1931-2025). Skill = P(outcome|condition) − P(outcome|¬condition), median
splits, 1000-permutation two-sided p, Benjamini-Hochberg FDR q < 0.10.

- **10 of 76 rules FDR-significant** (expected false discoveries if all
  were null: ~1.0). Mean |skill| across all rules: 0.117.
- Sensitivity (post hoc): trimming outcome windows of any day inside the
  condition window leaves **8** significant (expected ~0.8).

Full tables: `outputs/census.json`, `outputs/census_trimmed.json`.

## Reference points (post hoc, 2026-11): `src/baselines.py`

For each rule: year-bootstrap 95% CI of skill; skill on CET from 1878 only
(earlier CET rests on fewer, less homogeneous stations); skill after
removing a 31-year running mean (trend); skill of the persistence rule;
skill given persistence (stratified permutation, only defined when the
two sides use different variables); and the |skill| percentile among 200
random rules of the same shape. Output: `outputs/baselines.json`.

| proverb (abridged) | skill [95% CI] | 1878+ | detrended | persistence | pct. among random |
|---|---|---|---|---|---|
| Thunderstorms early August -> rain follows (precip) | +0.41 [+0.22, +0.60] | +0.41 | +0.45* | +0.45 | 0.63 |
| St. Matthias breaks the ice; if none, he will make it | −0.30 [−0.41, −0.18] | −0.30 | −0.34* | +0.34 | 0.84 |
| Freezes on St. Matthias' Day -> freezes for a month | +0.30 [+0.20, +0.42] | +0.30 | +0.34* | +0.34 | 0.88 |
| Cold at St. Peter's Day -> it will last longer | +0.28 [+0.14, +0.40] | +0.28 | +0.31* | +0.31 | 0.88 |
| Frost on the shortest day -> severe winter | +0.21 [+0.09, +0.33] | +0.19 | +0.18* | +0.18 | 0.67 |
| Ice bears a man before Christmas -> not a mouse after | −0.21 [−0.34, −0.08] | −0.05 | −0.15 | +0.15 | 0.39 |
| Cold spell in September without frost -> ... | +0.20 [+0.07, +0.32] | +0.14 | +0.02 | +0.02 | 0.03 |
| Heavy frosts in October -> January ... | −0.20 [−0.32, −0.07] | −0.05 | +0.06 | −0.06 | 0.40 |
| So many frosts in March, so many in May | +0.17 [+0.04, +0.28] | +0.14 | +0.07 | +0.07 | 0.48 |
| All Saints' winter -> St. Martin's summer | −0.17 [−0.29, −0.04] | −0.16 | −0.15 | +0.15 | 0.78 |

\* FDR-significant after detrending. Rows: the 10 census-significant rules.
Persistence = skill of "the outcome variable keeps its condition-window
anomaly"; for same-variable rules the detrended skill equals it (or its
negative, when the proverb predicts a reversal) by construction.

## Limits

- One collection, one chapter (calendar proverbs); sky/wind/animal lore
  is untestable against these two variables and was excluded by design.
- Coarse mappings (fine->dry, frost->cold) flatten some nuances.
- Precipitation rules see only 94 years (1931-); temp rules see 253.
- Every significant rule is a persistence rule (see Reference points), so
  the census measures which proverbs restate persistence and which deny
  it; it does not show skill beyond a persistence forecast.
- The 25-rule fidelity audit had one rater (the author); no second rater
  and no kappa. A second, independent rating is the main open item.
- The extraction depends on a closed model (`claude-sonnet-5`, CLI, no
  temperature control, one run); `outputs/extracted.jsonl` and
  `outputs/chunks.json` cache its exact output, and `src/extract.py` holds
  the prompt.

## What would extend it

The other chapters (sky colour vs sunshine hours, wind lore vs reanalysis
winds), other national corpora against their own national series, and
lead-time profiling of the confirmed rules.
