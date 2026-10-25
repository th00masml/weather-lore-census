# Results — the Weather Lore Census

Run date: 2026-08-10. Extraction model: `claude-sonnet-5` (authenticated
CLI, no API key), used ONLY as a parser. Evaluation: deterministic, no
model. Everything recomputes from cached `outputs/`.

## Verdict: BUILT

Both preregistered gates passed, and the census finds real, FDR-surviving
forecasting skill in a subset of Victorian weather proverbs — alongside a
clean quantitative refutation of another subset. Inwards' 1898 corpus has
its "test of experience", 128 years late.

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

## The census (primary, as preregistered)

76 rules, each tested on up to 254 years of daily Central England
Temperature (1772-2025) and 94 years of daily England-Wales precipitation
(1931-2025). Skill = P(outcome|condition) − P(outcome|¬condition), median
splits, 1000-permutation two-sided p, Benjamini-Hochberg FDR q < 0.10.

- **11 of 76 rules FDR-significant** (expected false discoveries if all
  were null: ~1.1). Mean |skill| across all rules: 0.123.
- Sensitivity analysis (post-hoc, disclosed): trimming outcome windows of
  any day inside the condition window (removing self-inclusion
  autocorrelation) leaves **9 FDR-significant** (expected ~0.9). The
  signal is not an overlap artifact.

Full tables: `outputs/census.json` (primary), `outputs/census_trimmed.json`
(sensitivity). Reproduce:

```
cd src
python extract.py && python audit.py
python evaluate.py && python sensitivity.py
```

## What the Victorians got right — and exactly wrong

The FDR-surviving rules tell one coherent story: **English winter weather
persists, and the lore that encoded persistence is true, while the lore
that promised reversal is refuted — with the opposite sign.**

Confirmed (positive skill, trimmed analysis, n = years):

| proverb | skill | p | n |
|---|---|---|---|
| "If it freezes on St. Matthias' Day (Feb 24), it will freeze for a month together" | +0.28 | <0.001 | 254 |
| "If cold at St. Peter's Day (Feb 22), it will last longer (forty days)" | +0.26 | <0.001 | 254 |
| "If St. Vitus's Day (Jun 15) be rainy, it will rain thirty days together" | +0.26 | 0.020 | 95 |
| "Frost on the shortest day indicates a severe winter" | +0.20 | <0.001 | 253 |

Refuted with opposite sign (the data shows persistence where the proverb
promised reversal):

| proverb | skill | p | n |
|---|---|---|---|
| "St. Matthias breaks the ice; if he finds none, he will make it" | **−0.28** | <0.001 | 254 |
| "If ice will bear a man before Christmas, it will not bear a mouse after" | **−0.21** | 0.003 | 254 |

A cold late-February day genuinely predicts a cold month (254 years of
data); a mild one predicts a mild month — the "he will make it" reversal
is anti-true. Most of the corpus (65/76 rules), including nearly all
long-range seasonal prophecies ("wet September, drought next summer",
"warm October, cold February"), shows no detectable skill: quantified
refutation at corpus scale, for the first time.

## Why the instrument mattered

The LLM did what no one had done since 1898: converted an archaic verse
corpus into 76 precise, dated, machine-testable forecasting rules in ~25
minutes. The judging was done entirely by 253 years of instrument data.
Memorization is structurally irrelevant: the model never saw a weather
number, and its beliefs cannot alter what HadCET says.

## Limits

- One collection, one chapter (calendar proverbs); sky/wind/animal lore
  is untestable against these two variables and was excluded by design.
- Coarse mappings (fine->dry, frost->cold) flatten some nuances.
- Precipitation rules see only 94 years (1931-); temp rules see 253.
- The persistence findings are consistent with known midlatitude weather
  autocorrelation — the novelty is showing *which specific proverbs*
  encode it, and which claim the opposite of reality, corpus-wide with
  FDR control.

## What would extend it

The other chapters (sky colour vs sunshine hours, wind lore vs reanalysis
winds), other national corpora against their own national series, and
lead-time profiling of the confirmed rules.
