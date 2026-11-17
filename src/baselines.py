"""Is the proverbs' skill more than persistence and trend? (added 2026-11, post hoc)

The census (evaluate.py) scores each rule against "condition false" years. It
does not ask whether a proverb knows anything beyond two facts that need no
lore at all: weather anomalies persist for weeks (persistence), and 254 years
of CET contain a warming trend that makes any two windows of the same year
co-vary. This script adds three reference points, for every evaluable rule:

1. Trend: the skill recomputed after removing a 31-year centred running mean
   from each window series before the median split.
2. Persistence: the skill of the trivial rule "the outcome variable keeps the
   anomaly it had during the condition window" (same years, same windows),
   and the proverb's skill conditional on that persistence predictor
   (stratified permutation: the condition is shuffled only among years with
   the same persistence value, 2000 permutations).
3. Random rules: 200 rules per proverb with the same variables, window lengths
   and lag, at a random calendar position and with random directions, scored
   the same way (detrended). The proverb's |skill| percentile among them says
   whether the folk calendar picked better dates than chance.

BH-FDR at q < 0.10 as in the census. Writes outputs/baselines.json.
Deterministic (seed 0), numpy only, about a minute.
"""
import datetime as dt
import json
import os

import numpy as np

from evaluate import load_series, RAW, OUT, FDR_Q

N_PERM = 2000
N_RANDOM = 200
TREND_WINDOW = 31
REF = [dt.date(2001, 1, 1) + dt.timedelta(days=i) for i in range(365)]   # non-leap calendar, as evaluate.py
DOY = {(d.month, d.day): i for i, d in enumerate(REF)}


def to_grid(series):
    years = sorted({y for (y, _, _) in series})
    g = np.full((len(years), 365), np.nan)
    for (y, m, d), v in series.items():
        if (m, d) in DOY:
            g[y - years[0], DOY[(m, d)]] = v
    return years[0], g


def window_idx(start, length):
    """Day indices (row offset 0 or 1, column) for a window of `length` days from doy `start`."""
    cols = (start + np.arange(length)) % 365
    rows = (start + np.arange(length)) // 365
    return rows, cols


def doy_of(mmdd):
    return DOY[(int(mmdd[:2]), min(int(mmdd[3:]), 28) if mmdd[:2] == "02" else int(mmdd[3:]))]


def win_len(a, b):
    sa, sb = doy_of(a), doy_of(b)
    return (sb - sa) % 365 + 1


def window_series(y0, grid, years, start, length, agg):
    rows, cols = window_idx(start, length)
    out = np.full(len(years), np.nan)
    for k, y in enumerate(years):
        r = y - y0 + rows
        if r.max() >= grid.shape[0] or r.min() < 0:
            continue
        v = grid[r, cols]
        ok = ~np.isnan(v)
        if ok.sum() < max(1, int(0.8 * length)):
            continue
        out[k] = v[ok].mean() if agg == "mean" else v[ok].sum()
    return out


def detrend(x, w=TREND_WINDOW):
    s = np.full_like(x, np.nan)
    h = w // 2
    for i in range(len(x)):
        seg = x[max(0, i - h): i + h + 1]
        seg = seg[~np.isnan(seg)]
        if len(seg) >= 10:
            s[i] = seg.mean()
    return x - s


def binarise(x, direction):
    med = np.nanmedian(x)
    return x > med if direction == "above" else x < med


def skill(c, o):
    if c.sum() in (0, len(c)):
        return np.nan
    return float(o[c].mean() - o[~c].mean())


def perm_p(c, o, rng, strata=None):
    obs = skill(c, o)
    if np.isnan(obs):
        return np.nan, np.nan
    null = np.empty(N_PERM)
    cc = c.copy()
    for i in range(N_PERM):
        if strata is None:
            rng.shuffle(cc)
        else:
            for s in (True, False):
                idx = np.where(strata == s)[0]
                cc[idx] = rng.permutation(c[idx])
        null[i] = skill(cc, o)
    return obs, float((np.abs(null) >= abs(obs)).mean())


def cond_skill(c, o, p):
    """Weighted mean of within-stratum skills (strata = persistence predictor)."""
    vals, ws = [], []
    for s in (True, False):
        m = p == s
        sk = skill(c[m], o[m])
        if not np.isnan(sk):
            vals.append(sk); ws.append(m.sum())
    return float(np.average(vals, weights=ws)) if vals else np.nan


def cond_perm_p(c, o, p, rng):
    obs = cond_skill(c, o, p)
    null = np.empty(N_PERM)
    cc = c.copy()
    for i in range(N_PERM):
        for s in (True, False):
            idx = np.where(p == s)[0]
            cc[idx] = rng.permutation(c[idx])
        null[i] = cond_skill(cc, o, p)
    return obs, float((np.abs(null) >= abs(obs)).mean())


def bh(ps, q=FDR_Q):
    ps = np.asarray(ps, dtype=float)
    order = np.argsort(ps)
    m = len(ps)
    thr = 0.0
    for rank, i in enumerate(order, 1):
        if ps[i] <= q * rank / m:
            thr = ps[i]
    return [bool(p <= thr and thr > 0) for p in ps]


def main():
    grids = {"temp": to_grid(load_series(os.path.join(RAW, "cet_daily.txt"))),
             "precip": to_grid(load_series(os.path.join(RAW, "ewp_daily.txt")))}
    agg = {"temp": "mean", "precip": "sum"}
    yr_min = {"temp": 1772, "precip": 1931}
    yr_max = min(grids["temp"][0] + grids["temp"][1].shape[0], grids["precip"][0] + grids["precip"][1].shape[0]) - 1
    census = [r for r in json.load(open(os.path.join(OUT, "census.json"))) if r["status"] == "ok"]
    rng = np.random.default_rng(0)
    out = []
    for r in census:
        cv, ov = r["cond"]["var"], r["out"]["var"]
        years = list(range(max(yr_min[cv], yr_min[ov]), yr_max))
        cs, cl = doy_of(r["cond"]["start"]), win_len(r["cond"]["start"], r["cond"]["end"])
        os_, ol = doy_of(r["out"]["start"]), win_len(r["out"]["start"], r["out"]["end"])
        lag = (os_ - cs) % 365
        c_raw = window_series(*grids[cv], years, cs, cl, agg[cv])
        o_raw = window_series(*grids[ov], years, cs + lag, ol, agg[ov])
        p_raw = window_series(*grids[ov], years, cs, cl, agg[ov])      # persistence: outcome variable over the condition window
        keep = ~np.isnan(c_raw) & ~np.isnan(o_raw) & ~np.isnan(p_raw)
        c_raw, o_raw, p_raw = c_raw[keep], o_raw[keep], p_raw[keep]
        c, o = binarise(c_raw, r["cond"]["dir"]), binarise(o_raw, r["out"]["dir"])
        sk, p = perm_p(c, o, rng)
        cd_, od_, pd_ = detrend(c_raw), detrend(o_raw), detrend(p_raw)
        kd = ~np.isnan(cd_) & ~np.isnan(od_) & ~np.isnan(pd_)
        c_d, o_d = binarise(cd_[kd], r["cond"]["dir"]), binarise(od_[kd], r["out"]["dir"])
        p_d = binarise(pd_[kd], r["out"]["dir"])
        sk_d, p_dp = perm_p(c_d, o_d, rng)
        pers, pers_p = perm_p(p_d, o_d, rng)
        # when condition and outcome use the same variable, the condition window IS the persistence
        # predictor (up to direction), so a skill "beyond persistence" is undefined, not zero
        same_info = cv == ov
        csk, cp = (None, None) if same_info else cond_perm_p(c_d, o_d, p_d, rng)
        # uncertainty: bootstrap over years; and the post-1878 part of CET only (pre-1878 CET is
        # built from fewer, less homogeneous stations)
        boot = []
        for _ in range(1000):
            ix = rng.integers(0, len(c), len(c))
            boot.append(skill(c[ix], o[ix]))
        yrs = np.array(years)[keep]
        late = yrs >= 1878
        sk_late = skill(binarise(c_raw[late], r["cond"]["dir"]), binarise(o_raw[late], r["out"]["dir"])) if late.sum() >= 30 else None
        # random rules: same variables, lengths and lag; random start and directions; detrended
        rnd = []
        for _ in range(N_RANDOM):
            s0 = int(rng.integers(0, 365))
            dc, do = rng.choice(["above", "below"], 2)
            a = detrend(window_series(*grids[cv], years, s0, cl, agg[cv]))
            b = detrend(window_series(*grids[ov], years, s0 + lag, ol, agg[ov]))
            k = ~np.isnan(a) & ~np.isnan(b)
            rnd.append(abs(skill(binarise(a[k], dc), binarise(b[k], do))))
        rnd = np.array([x for x in rnd if not np.isnan(x)])
        out.append({"quote": r["quote"], "cond": r["cond"], "out": r["out"], "n_years": int(keep.sum()),
                    "census_skill": r["skill"], "census_fdr": r.get("fdr_significant", False),
                    "skill": sk, "p": p, "skill_ci95_years_bootstrap": [float(x) for x in np.nanpercentile(boot, [2.5, 97.5])],
                    "skill_1878_onwards": sk_late, "skill_detrended": sk_d, "p_detrended": p_dp,
                    "persistence_skill": pers, "persistence_p": pers_p,
                    "skill_given_persistence": csk, "p_given_persistence": cp,
                    "condition_is_persistence": same_info,
                    "random_rules_abs_skill_median": float(np.median(rnd)),
                    "random_rules_abs_skill_p95": float(np.percentile(rnd, 95)),
                    "percentile_among_random": float((rnd < abs(sk_d)).mean())})
    for key, fk in (("p", "fdr"), ("p_detrended", "fdr_detrended"), ("p_given_persistence", "fdr_given_persistence")):
        sub = [r for r in out if r[key] is not None]
        for r, f in zip(sub, bh([r[key] for r in sub])):
            r[fk] = f
        for r in out:
            r.setdefault(fk, None)
    summary = {"n_rules": len(out),
               "fdr_census_recomputed": sum(r["fdr"] for r in out),
               "fdr_detrended": sum(r["fdr_detrended"] for r in out),
               "rules_condition_is_persistence": sum(r["condition_is_persistence"] for r in out),
               "rules_with_other_variable": sum(not r["condition_is_persistence"] for r in out),
               "fdr_given_persistence_other_variable": sum(bool(r["fdr_given_persistence"]) for r in out),
               "census_vs_recomputed_max_abs_diff": float(max(abs(r["skill"] - r["census_skill"]) for r in out)),
               "rules_above_random_p95_expected_by_chance": 0.05 * len(out),
               "mean_abs_skill_detrended": float(np.mean([abs(r["skill_detrended"]) for r in out])),
               "mean_abs_skill_random_rules_median": float(np.mean([r["random_rules_abs_skill_median"] for r in out])),
               "rules_above_random_p95": sum(abs(r["skill_detrended"]) > r["random_rules_abs_skill_p95"] for r in out),
               "settings": {"n_boot_years": 1000, "n_perm": N_PERM, "n_random": N_RANDOM, "trend_window_years": TREND_WINDOW, "fdr_q": FDR_Q, "seed": 0}}
    json.dump({"summary": summary, "rules": out}, open(os.path.join(OUT, "baselines.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))
    print("\nrules significant in the census, with the three reference points:")
    for r in sorted(out, key=lambda r: -abs(r["skill"])):
        if r["census_fdr"]:
            print(f"  {r['skill']:+.2f} detr {r['skill_detrended']:+.2f}{'*' if r['fdr_detrended'] else ' '} "
                  f"pers {r['persistence_skill']:+.2f} | given pers {'same var' if r['condition_is_persistence'] else format(r['skill_given_persistence'], '+.2f')}{'*' if r['fdr_given_persistence'] else ' '} "
                  f"pct-rand {r['percentile_among_random']:.2f} | {r['quote'][:60]}")


if __name__ == "__main__":
    main()
