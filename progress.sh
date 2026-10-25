#!/bin/bash
cd "$(dirname "$0")"
count(){ if [ -f "$1" ]; then wc -l < "$1" | tr -d ' '; else echo 0; fi; }
bar(){ local d=$1 t=$2 w=32 f=0 p=0; if [ "$t" -gt 0 ]; then f=$((d*w/t)); p=$((d*100/t)); fi
  printf "%-11s [" "$3"; for ((i=0;i<w;i++)); do if [ $i -lt $f ]; then printf '#'; else printf '-'; fi; done
  printf "] %d/%d (%d%%)\n" "$d" "$t" "$p"; }
echo "RUN 8  weather-lore-census  —  $(date +%H:%M:%S)"
bar "$(count outputs/extracted.jsonl)" 75 "extract"
nr=0
if [ -f outputs/extracted.jsonl ]; then
  nr=$(python3 -c "import json,sys;print(sum(json.loads(l)['n'] for l in open('outputs/extracted.jsonl')))" 2>/dev/null || echo 0)
fi
echo "rules extracted so far: $nr"
if grep -q EXTRACT_DONE outputs/extract.log 2>/dev/null; then echo "STATUS: extraction complete"; else echo "STATUS: running"; fi
