#!/usr/bin/env python3
"""Assert every worked example in README.md actually encodes its own sentence.

This exists because the flagship example was WRONG from the first commit until
2026-08-30: `fails` (5 letters) was drawn with 4 symbols and `beautifully` (11) with
10. Nobody caught it in years, because a run of identical marks is not readable by
eye — which is exactly the property the encoding is built on. A channel whose errors
are invisible to its own authors needs a machine to check it.

    python3 test_readme_examples.py
"""
import re
import sys

BLOCK = re.compile(r"```\n([^\n]+)\n\n((?:\S.*\n)+?)```")
ROW = re.compile(r"^(\S+)\s+(·+)\s+(\d+)\s*$")


def check(path="README.md"):
    text = open(path, encoding="utf-8").read()
    blocks = BLOCK.findall(text)
    if not blocks:
        print("FAIL: no worked example found in", path)
        return 1

    failures = 0
    checked = 0
    for sentence, body in blocks:
        rows = [ROW.match(l) for l in body.splitlines() if l.strip()]
        if not all(rows):
            continue  # not a worked example; some other fenced block
        words = sentence.split()
        if len(words) != len(rows):
            print(f"FAIL: {sentence!r} has {len(words)} words but {len(rows)} rows")
            failures += 1
            continue
        for word, m in zip(words, rows):
            shown_word, dots, num = m.group(1), m.group(2), int(m.group(3))
            checked += 1
            if shown_word != word:
                print(f"FAIL: row says {shown_word!r}, sentence says {word!r}")
                failures += 1
            elif len(dots) != len(word):
                print(f"FAIL: {word!r} is {len(word)} letters, drawn with {len(dots)}")
                failures += 1
            elif num != len(word):
                print(f"FAIL: {word!r} is {len(word)} letters, labelled {num}")
                failures += 1

    if not checked:
        print("FAIL: found blocks but no parsable example rows")
        return 1
    if failures:
        print(f"{failures} bad row(s) of {checked}")
        return 1
    print(f"ok: {checked} rows across {len(blocks)} block(s), all lengths agree")
    return 0


if __name__ == "__main__":
    sys.exit(check(*sys.argv[1:]))
