# weather-lore-census

Did the Victorian weather proverbs know anything? First corpus-scale test.

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

The verdict on every proverb comes from the sky, not from the model —
memorization is structurally irrelevant.

- Preregistration (kill criterion = extraction yield + fidelity): `PROBLEM.md`
- Licenses (Inwards PD; Met Office OGL): `DATA-LICENSES.md`
- The census + verdict: `RESULTS.md`
- Live progress: `./progress.sh`

## Run it

```
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
# data/raw/: inwards.txt (archive.org), cet_daily.txt + ewp_daily.txt (Met Office)

cd src
python extract.py    # model: proverbs -> rules (cached)
python audit.py      # fidelity sample for human judgment
python evaluate.py   # deterministic census: skill, permutation p, FDR
```
