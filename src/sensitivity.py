"""Post-hoc sensitivity (disclosed as such in RESULTS.md): re-run the census
with outcome windows TRIMMED of any day inside the condition window, removing
self-inclusion autocorrelation. Primary analysis stays as preregistered."""
import datetime as dt
import json
import os

import numpy as np

from evaluate import load_series, window_days, window_value, valid_rule, RAW, OUT, N_PERM, MIN_YEARS, FDR_Q


def main():
    temp = load_series(os.path.join(RAW, "cet_daily.txt"))
    prec = load_series(os.path.join(RAW, "ewp_daily.txt"))
    series = {"temp": temp, "precip": prec}
    agg = {"temp": "mean", "precip": "sum"}
    yr_min = {"temp": 1772, "precip": 1931}
    yr_max = min(max(y for (y, _, _) in temp), max(y for (y, _, _) in prec))

    raw = []
    for l in open(os.path.join(OUT, "extracted.jsonl")):
        raw += json.loads(l)["rules"]
    rules, seen = [], set()
    for r in raw:
        if not valid_rule(r) or r["cond"] == r["out"]:
            continue
        key = json.dumps([r["cond"], r["out"]], sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        rules.append(r)

    rng = np.random.default_rng(0)
    ok = []
    trimmed_away = 0
    for r in rules:
        cd, cw = window_days(r["cond"]["start"], r["cond"]["end"])
        od, ow = window_days(r["out"]["start"], r["out"]["end"])
        cset = set(cd)
        od2 = [d for d in od if d not in cset]
        if not od2:
            trimmed_away += 1
            continue
        y0 = max(yr_min[r["cond"]["var"]], yr_min[r["out"]["var"]])
        cvals, ovals = [], []
        for y in range(y0, yr_max):
            cv = window_value(series[r["cond"]["var"]], y, cd, cw, agg[r["cond"]["var"]])
            ov = window_value(series[r["out"]["var"]], y, od2, ow, agg[r["out"]["var"]])
            if cv is not None and ov is not None:
                cvals.append(cv); ovals.append(ov)
        n = len(cvals)
        if n < MIN_YEARS:
            continue
        cvals = np.array(cvals); ovals = np.array(ovals)
        cbin = cvals > np.median(cvals) if r["cond"]["dir"] == "above" else cvals < np.median(cvals)
        obin = ovals > np.median(ovals) if r["out"]["dir"] == "above" else ovals < np.median(ovals)
        if cbin.sum() in (0, n):
            continue
        skill = float(obin[cbin].mean() - obin[~cbin].mean())
        ob = obin.copy()
        perm = np.empty(N_PERM)
        for i in range(N_PERM):
            rng.shuffle(ob)
            perm[i] = ob[cbin].mean() - ob[~cbin].mean()
        p = float((np.abs(perm) >= abs(skill)).mean())
        ok.append({"quote": r["quote"], "skill": round(skill, 4), "p": round(p, 4), "n": n})

    ps = sorted(r["p"] for r in ok)
    m = len(ps)
    thresh = 0.0
    for rank, p in enumerate(ps, 1):
        if p <= FDR_Q * rank / m:
            thresh = p
    nsig = sum(r["p"] <= thresh for r in ok) if thresh > 0 else 0
    json.dump(ok, open(os.path.join(OUT, "census_trimmed.json"), "w"), indent=1)
    print(f"trimmed census: {len(ok)} rules ({trimmed_away} fully-overlapping dropped)")
    print(f"FDR q<{FDR_Q}: {nsig} significant (expected false ~ {FDR_Q*nsig:.1f})")
    for r in sorted(ok, key=lambda r: -abs(r["skill"]))[:8]:
        if r["p"] <= 0.05:
            print(f"  skill={r['skill']:+.3f} p={r['p']:.3f} n={r['n']} | {r['quote'][:70]}")


if __name__ == "__main__":
    main()
