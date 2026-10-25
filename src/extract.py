"""Extract machine-testable rules from the 'Times and Seasons' chapter of
Inwards 1898 using claude-sonnet-5. The model is a parser: prose -> JSON
rules. Cached per chunk / resume-safe."""
import json
import os
import re
import time

from common import generate_cli

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "data/raw/inwards.txt")
OUT = os.path.join(ROOT, "outputs")
CHUNKS = os.path.join(OUT, "chunks.json")
RES = os.path.join(OUT, "extracted.jsonl")
CHUNK_LINES = 55

SYSTEM = "You convert archaic English weather proverbs into machine-testable rules. Output ONLY a JSON array, no prose, no code fences."

USER = '''Below is OCR text from Inwards' "Weather Lore" (1898), calendar section. Extract every proverb that makes a TESTABLE conditional weather prediction for England, i.e. BOTH sides map to daily TEMPERATURE or PRECIPITATION in date windows:
- condition: weather in a calendar window (a saint's day, month, or season)
- outcome: LATER weather in a calendar window (within 12 months)

Map language: fine/clear/bright/dry/sunny -> precip "below"; rain/wet/foul/showers -> precip "above"; cold/frost/ice/snow -> temp "below"; warm/mild/hot -> temp "above". Use the traditional date for named days (Candlemas=02-02, St. Swithin=07-15, St. Martin=11-11, Michaelmas=09-29, Christmas=12-25, St. Paul=01-25, St. Vincent=01-22, Lady Day=03-25, St. John=06-24, etc.). A bare month means the whole month.

Skip proverbs about sky colour, wind direction, moon, animals, harvest/crops, health, or anything not reducible to temp/precip windows: do NOT output them.

For each testable proverb output:
{{"quote":"<=120 chars of the proverb", "cond":{{"start":"MM-DD","end":"MM-DD","var":"temp|precip","dir":"above|below"}}, "out":{{"start":"MM-DD","end":"MM-DD","var":"temp|precip","dir":"above|below"}}}}

If the outcome window falls earlier in the calendar than the condition window, it belongs to the NEXT year (that is fine, just give the dates).

TEXT:
"""
{chunk}
"""

JSON array only:'''


def get_chapter():
    lines = open(RAW, encoding="utf-8", errors="ignore").read().split("\n")
    # chapter runs from the first "January." heading to the Sun/Moon section
    start = next(i for i, l in enumerate(lines) if re.match(r"^\s*January\.\s*$", l))
    end = None
    for i in range(start, len(lines)):
        if re.search(r"Sun,\s+Moon,\s+and\s+Stars", lines[i]) or \
           re.match(r"^\s*SUN,\s+MOON", lines[i]):
            end = i
            break
    if end is None:
        end = start + 4200
    return lines[start:end]


def main():
    os.makedirs(OUT, exist_ok=True)
    lines = get_chapter()
    print(f"chapter lines: {len(lines)}")
    chunks = []
    for i in range(0, len(lines), CHUNK_LINES):
        txt = "\n".join(lines[i:i + CHUNK_LINES]).strip()
        if len(txt) > 100:
            chunks.append(txt)
    json.dump(chunks, open(CHUNKS, "w"))
    print(f"chunks: {len(chunks)}")

    done = set()
    if os.path.exists(RES):
        for l in open(RES):
            done.add(json.loads(l)["chunk"])
    f = open(RES, "a")
    t0 = time.time()
    for ci, chunk in enumerate(chunks):
        if ci in done:
            continue
        out = generate_cli(USER.format(chunk=chunk), system=SYSTEM,
                           model="claude-sonnet-5", timeout=180)
        s = out.strip()
        s = re.sub(r"^```(json)?|```$", "", s, flags=re.M).strip()
        try:
            rules = json.loads(s)
            if not isinstance(rules, list):
                rules = []
        except Exception:
            rules = []
        f.write(json.dumps({"chunk": ci, "n": len(rules), "rules": rules}) + "\n")
        f.flush()
        print(f"[{ci+1}/{len(chunks)}] +{len(rules)} rules  {time.time()-t0:.0f}s", flush=True)
    f.close()
    total = sum(json.loads(l)["n"] for l in open(RES))
    print(f"raw extracted rules: {total}")


if __name__ == "__main__":
    main()
