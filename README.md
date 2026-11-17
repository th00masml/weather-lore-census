# weather-lore-census

Did the Victorian weather proverbs know anything? A corpus-scale test.

In 1898 Richard Inwards published *Weather Lore*, thousands of collected
proverbs whose truth he left "to the test of experience". That test never
happened — formalising archaic verse into testable rules at scale was
nobody's idea of a feasible project, and the long daily weather series
needed to judge them barely existed.

This repo runs the census:

1. `claude-sonnet-5` reads the calendar chapter and converts each proverb
   into a machine-testable rule (condition window/variable/direction →
   predicted later window/variable/direction). The model is a **parser,
   not a judge** — it never sees any weather data.
2. A deterministic evaluator tests every rule against **253 years** of
   daily Central England Temperature (HadCET, 1772–) and **94 years** of
   daily England & Wales precipitation (HadEWP, 1931–), with permutation
   nulls and Benjamini–Hochberg FDR.

The verdict on every proverb comes from the sky, not from the model, so
memorization is structurally irrelevant.

**Result (revised 2026-11):** 10 of 76 rules are FDR-significant, and every
one of them restates persistence (the condition and outcome use the same
variable, and the proverb's skill equals that of "the anomaly carries
on"). None of the cross-variable rules adds skill beyond persistence, and
as a corpus the proverbs pick dates no better than random rules of the same
shape. Two evaluator bugs were fixed on the way; see `RESULTS.md`.

- Preregistration (kill criterion = extraction yield + fidelity): `PROBLEM.md`
- Licenses (Inwards PD; Met Office OGL): `DATA-LICENSES.md`
- The census + verdict: `RESULTS.md`
- Live progress: `./progress.sh`
- Code licence: MIT (`LICENSE`); data checksums: `DATA-SHA256.txt`

## Run it

```
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
# data/raw/: inwards.txt (archive.org), cet_daily.txt + ewp_daily.txt (Met Office)

cd src
python extract.py    # model: proverbs -> rules (cached)
python audit.py      # fidelity sample for human judgment
python evaluate.py   # deterministic census: skill, permutation p, FDR
python sensitivity.py  # outcome windows trimmed of condition days
python baselines.py  # persistence, trend, random-rule reference points (~1 min)
cd .. && python -m pytest tests   # needs pytest; evaluator fixes are pinned here
```

The data files used for the published numbers (downloaded 2026-08-10,
series through 2026-08-07) are identified by `DATA-SHA256.txt`.
