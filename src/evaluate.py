"""Deterministic census: validate + dedup extracted rules, evaluate each on
HadCET (temp, 1772-) / HadEWP (precip, 1931-), permutation nulls, BH-FDR.
No model calls."""
import datetime as dt
import json
import os
import re

import numpy as np

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "data/raw")
OUT = os.path.join(ROOT, "outputs")
N_PERM = 1000
MIN_YEARS = 30
FDR_Q = 0.10


def load_series(path):
    vals = {}
    for l in open(path, encoding="utf-8", errors="ignore"):
        m = re.match(r"\s*(\d{4})-(\d{2})-(\d{2})\s+(-?\d+\.?\d*)", l)
        if m:
            y, mo, d, v = int(m[1]), int(m[2]), int(m[3]), float(m[4])
            if v <= -99:
                continue
            vals[(y, mo, d)] = v
    return vals


def window_days(start, end):
    """Return list of (month, day) from start MM-DD to end MM-DD inclusive,
    wrapping over new year if needed. Uses a non-leap reference year."""
    s = dt.date(2001, int(start[:2]), int(start[3:]))
    e = dt.date(2001, int(end[:2]), int(end[3:]))
    days = []
    cur = s
    while True:
        days.append((cur.month, cur.day))
        if cur == e:
            break
        cur += dt.timedelta(days=1)
        if cur == s:  # full wrap safety
            break
        if len(days) > 366:
            break
    return days, e < s  # wrapped?


def window_value(series, year, days, wrapped, agg):
    vs = []
    y = year
    prev = None
    for (mo, d) in days:
        if prev and (mo, d) < prev and wrapped:
            y = year + 1
        prev = (mo, d)
        v = series.get((y, mo, d))
        if v is not None:
            vs.append(v)
    if len(vs) < max(1, int(0.8 * len(days))):
        return None
    return float(np.mean(vs)) if agg == "mean" else float(np.sum(vs))


def valid_rule(r):
    try:
        for side in ("cond", "out"):
            s = r[side]
            assert s["var"] in ("temp", "precip") and s["dir"] in ("above", "below")
            for k in ("start", "end"):
                mm, dd = int(s[k][:2]), int(s[k][3:])
                assert 1 <= mm <= 12 and 1 <= dd <= 31
                dt.date(2001, mm, min(dd, 28))
        return True
    except Exception:
        return False


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
        if not valid_rule(r):
            continue
        key = (r["cond"]["start"], r["cond"]["end"], r["cond"]["var"], r["cond"]["dir"],
               r["out"]["start"], r["out"]["end"], r["out"]["var"], r["out"]["dir"])
        if key in seen or (r["cond"] == r["out"]):
            continue
        seen.add(key)
        rules.append(r)
    print(f"raw {len(raw)} -> valid+dedup {len(rules)}")

    rng = np.random.default_rng(0)
    results = []
    for r in rules:
        cd, cw = window_days(r["cond"]["start"], r["cond"]["end"])
        od, ow = window_days(r["out"]["start"], r["out"]["end"])
        y0 = max(yr_min[r["cond"]["var"]], yr_min[r["out"]["var"]])
        cvals, ovals, years = [], [], []
        for y in range(y0, yr_max):
            cv = window_value(series[r["cond"]["var"]], y, cd, cw, agg[r["cond"]["var"]])
            ov = window_value(series[r["out"]["var"]], y, od, ow, agg[r["out"]["var"]])
            if cv is not None and ov is not None:
                cvals.append(cv); ovals.append(ov); years.append(y)
        n = len(years)
        if n < MIN_YEARS:
            results.append({**r, "n_years": n, "status": "insufficient-data"})
            continue
        cvals = np.array(cvals); ovals = np.array(ovals)
        cbin = cvals > np.median(cvals) if r["cond"]["dir"] == "above" else cvals < np.median(cvals)
        obin = ovals > np.median(ovals) if r["out"]["dir"] == "above" else ovals < np.median(ovals)
        if cbin.sum() in (0, n):
            results.append({**r, "n_years": n, "status": "degenerate"})
            continue
        skill = float(obin[cbin].mean() - obin[~cbin].mean())
        perm = np.empty(N_PERM)
        ob = obin.copy()
        for i in range(N_PERM):
            rng.shuffle(ob)
            perm[i] = ob[cbin].mean() - ob[~cbin].mean()
        p = float((np.abs(perm) >= abs(skill)).mean())
        results.append({**r, "n_years": n, "status": "ok",
                        "p_cond": float(cbin.mean()), "skill": round(skill, 4),
                        "p_value": round(p, 4)})

    ok = [r for r in results if r["status"] == "ok"]
    # Benjamini-Hochberg
    ps = sorted((r["p_value"], i) for i, r in enumerate(ok))
    m = len(ps)
    sig_idx = set()
    thresh = 0.0
    for rank, (p, i) in enumerate(ps, 1):
        if p <= FDR_Q * rank / m:
            thresh = p
    for i, r in enumerate(ok):
        r["fdr_significant"] = r["p_value"] <= thresh and thresh > 0
    n_sig = sum(r.get("fdr_significant", False) for r in ok)
    json.dump(results, open(os.path.join(OUT, "census.json"), "w"), indent=1)
    print(f"evaluable rules: {len(ok)}  (insufficient/degenerate: {len(results)-len(ok)})")
    print(f"FDR q<{FDR_Q}: {n_sig} significant  (expected false discoveries if all null ~ {FDR_Q*n_sig:.1f})")
    print(f"mean |skill| = {np.mean([abs(r['skill']) for r in ok]):.4f}")
    print("\ntop rules by |skill| (p<=0.05):")
    for r in sorted(ok, key=lambda r: -abs(r["skill"]))[:8]:
        if r["p_value"] <= 0.05:
            print(f"  skill={r['skill']:+.3f} p={r['p_value']:.3f} n={r['n_years']} fdr={r.get('fdr_significant')} | {r['quote'][:70]}")


if __name__ == "__main__":
    main()
