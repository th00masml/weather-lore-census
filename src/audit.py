"""Fidelity audit: sample 25 extracted rules (seed 0) and print quote vs
formalisation side by side for human judgment. Judgments are recorded in
RESULTS.md; this script only prepares the sample."""
import json
import os
import random

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "outputs")


def main():
    raw = []
    for l in open(os.path.join(OUT, "extracted.jsonl")):
        raw += json.loads(l)["rules"]
    seen, rules = set(), []
    for r in raw:
        k = json.dumps(r.get("cond", {}), sort_keys=True) + json.dumps(r.get("out", {}), sort_keys=True)
        if k in seen:
            continue
        seen.add(k)
        rules.append(r)
    rng = random.Random(0)
    sample = rng.sample(rules, min(25, len(rules)))
    json.dump(sample, open(os.path.join(OUT, "audit_sample.json"), "w"), indent=1)
    for i, r in enumerate(sample):
        c, o = r["cond"], r["out"]
        print(f"[{i+1:2}] \"{r['quote'][:90]}\"")
        print(f"     IF   {c['var']} {c['dir']} median in {c['start']}..{c['end']}")
        print(f"     THEN {o['var']} {o['dir']} median in {o['start']}..{o['end']}")


if __name__ == "__main__":
    main()
