#!/usr/bin/env python3
"""Stream a wikipedia dump to a plain-text corpus file, stopping at a TOKEN BUDGET.

Two languages must be matched on N. Plug-in entropy rises with sample size on a heavy
tail, so an unmatched corpus puts a sample-size difference straight into the column
labelled "language". Streaming also avoids pulling a whole dump: the ru download was
killed at 600s having fetched 555MB, and none of it was needed.

The budget counts tokens INSIDE ceiling.py's own 3-12-word sentence window, with
ceiling.py's own tokeniser, so the number budgeted is the number the estimator sees.
"""
import re, sys
from datasets import load_dataset

lang, target, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
WORD = re.compile(r"\b\w+\b", re.UNICODE)
SENT = re.compile(r"(?<=[.!?]) +")

d = load_dataset("wikimedia/wikipedia", f"20231101.{lang}", split="train", streaming=True)
tok = 0; docs = 0
with open(out, "w", encoding="utf-8") as f:
    for row in d:
        t = row["text"].replace("\n", " ").strip()
        if not t:
            continue
        for s in SENT.split(t):
            s = s.strip()
            if not s or "=" in s:
                continue
            n = len(WORD.findall(s))
            if 3 <= n <= 12:
                tok += n
        f.write(t + "\n"); docs += 1
        if tok >= target:
            break
print(f"{lang}: {docs} docs, {tok} in-window tokens -> {out}")
