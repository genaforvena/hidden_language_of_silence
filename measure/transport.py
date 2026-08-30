#!/usr/bin/env python3
"""
transport.py — which notation survives being SHOWN, and which one lies about it?

silent.py ships ONE notation. It was picked out of six candidates by this measurement,
not by taste -- the repository had already argued the question three times without ever
rendering one of them. The evidence has a shape worth stating before the numbers:

    "the medium preserved the bytes" and "the reader saw the message" are DIFFERENT
    CLAIMS, and the first one answers green while the second fails.

GitHub's markdown API returns `<p>(   ) (     ) (  ) (    )</p>` -- every space intact,
byte for byte. Read that and you conclude the bracket notation travels fine. Then a
browser lays it out under `white-space: normal`, and what a person actually reads is
`( ) ( ) ( ) ( )`: word lengths 3-5-2-4 arrive as 1-1-1-1. So the medium is measured
where a READER stands -- innerText after layout -- and never at the wire.

THREE OUTCOMES, and the middle one is the reason this file exists.

  intact              decoded lengths == the lengths that were sent.
  corrupted-loudly    the notation refuses to parse. Bad, but the reader KNOWS.
  corrupted-silently  it parses cleanly, into DIFFERENT lengths. The reader receives
                      another message and has no way to find out. `( )` is a perfectly
                      well-formed one-letter word.

A notation with no redundancy cannot ever be loud: whatever arrives is the message.
That is not a bug in the implementation, it is what "the channel is only the lengths"
costs, and it falls on `spaces` and `dots` as much as on `brackets`.
"""

import argparse, json, html, os, re, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance import Instrument            # noqa: E402
import silent                                # noqa: E402

INSTRUMENT = Instrument(__file__)

SENTENCE = "The night is long"

# The candidates. `block` is what silent.py ships, and it is taken FROM silent.py rather
# than restated here -- a second copy of the shipped notation would drift the day the
# mark changes, and this file's whole job is to be the reason that mark is what it is.
CANDIDATES = {
    "symbols":    (lambda ls: " ".join("\u25c6" * n for n in ls), " "),
    "spaces":     (lambda ls: "\t".join(" " * n for n in ls), "\t"),
    "brackets":   (lambda ls: " ".join("(" + " " * n + ")" for n in ls), None),
    "dots":       (lambda ls: " ".join("\u00b7" * n for n in ls), " "),
    "underscore": (lambda ls: " ".join("_" * n for n in ls), " "),
    "block":      (None, silent.WORD_SEP),
}


def _encode(form, sentence):
    if form == "block":
        return silent.encode(sentence)
    return CANDIDATES[form][0]([len(w) for w in sentence.split()])


def _lengths(form, encoded):
    """Decode a candidate. Only the shipped notation uses silent.lengths()."""
    if form == "block":
        return silent.lengths(encoded)
    sep = CANDIDATES[form][1]
    if sep is None:                      # brackets: the run's content IS the separator,
        import re                        # so it must be SCANNED, never split.
        runs = re.findall(r"\(( *)\)", encoded)
        rest = re.sub(r"\( *\)", "", encoded).strip()
        if rest or (not runs and encoded.strip()):
            raise ValueError("malformed bracket line")
        return [len(r) for r in runs]
    return [len(c) for c in encoded.split(sep) if c]

# A headless browser is the only honest reader for the html media. Playwright's bundled
# shell is used if present; a system chrome otherwise. Absent -> those media are `na`,
# never quietly dropped and never assumed to pass.
def _find_browser():
    for c in ("chrome-headless-shell", "google-chrome", "chromium", "chromium-browser"):
        p = shutil.which(c)
        if p:
            return p
    root = os.path.expanduser("~/.cache/ms-playwright")
    if os.path.isdir(root):
        for d in sorted(os.listdir(root), reverse=True):
            p = os.path.join(root, d, "chrome-headless-shell-linux64", "chrome-headless-shell")
            if os.path.exists(p):
                return p
    return None


BROWSER = _find_browser()


def _render_innertext(body_html, node_id="a"):
    """What a person reads: innerText after layout, not the bytes on the wire."""
    if not BROWSER:
        return None
    page = ("<!doctype html><meta charset=utf-8><body>" + body_html +
            "<script>document.title=JSON.stringify("
            f"document.getElementById('{node_id}').innerText)</script>")
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "t.html")
        open(f, "w", encoding="utf-8").write(page)
        p = subprocess.run([BROWSER, "--headless", "--disable-gpu", "--no-sandbox",
                            "--dump-dom", "file://" + f],
                           capture_output=True, text=True, timeout=120)
    m = re.search(r"<title>(.*?)</title>", p.stdout, re.S)
    if not m:
        return None
    return json.loads(html.unescape(m.group(1)))


# ------------------------------------------------------------------ media
def medium_file(enc):
    """Control arm. A round-trip through a file must be intact for every notation; if it
    is not, the harness is broken and no other row means anything."""
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "m.txt")
        open(f, "w", encoding="utf-8").write(enc)
        return open(f, encoding="utf-8").read()


def medium_html_flow(enc):
    return _render_innertext(f'<p id=a>{html.escape(enc)}</p>')


def medium_html_pre(enc):
    return _render_innertext(f'<pre id=a>{html.escape(enc)}</pre>')


def medium_markdown_github(enc):
    """GitHub's own renderer, then a browser. Both halves are needed: the API output is
    where the false green lives."""
    if not shutil.which("gh"):
        return None
    p = subprocess.run(["gh", "api", "-X", "POST", "/markdown",
                        "-f", "mode=markdown", "-f", "text=" + enc],
                       capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        return None
    return _render_innertext(f'<div id=a>{p.stdout}</div>')


def medium_markdown_github_wire(enc):
    """The SAME renderer read at the WIRE instead of at a reader. Present so the false
    green is on the table as a row rather than in a paragraph."""
    if not shutil.which("gh"):
        return None
    p = subprocess.run(["gh", "api", "-X", "POST", "/markdown",
                        "-f", "mode=markdown", "-f", "text=" + enc],
                       capture_output=True, text=True, timeout=120)
    if p.returncode != 0:
        return None
    m = re.search(r"<p>(.*?)</p>", p.stdout, re.S)
    return html.unescape(m.group(1)) if m else None


MEDIA = {
    "file (control)": medium_file,
    "html <p>": medium_html_flow,
    "html <pre>": medium_html_pre,
    "github md, at the wire": medium_markdown_github_wire,
    "github md, as read": medium_markdown_github,
}


def classify(form, sent_lengths, received):
    if received is None:
        return "na", None
    try:
        got = _lengths(form, received)
    except Exception:
        return "corrupted-loudly", None
    if got == sent_lengths:
        return "intact", got
    # ZERO WORDS IS LOUD. A decode that yields nothing at all is not a well-formed other
    # message -- there is no sentence with no words, so a reader hits it immediately. This
    # used to fall through to corrupted-silently, which put `spaces` under flowed HTML in
    # the same bucket as the bracket form, and the whole point of the middle verdict is
    # that it names the case a reader CANNOT detect.
    if not got:
        return "corrupted-loudly", got
    return "corrupted-silently", got


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sentence", default=SENTENCE)
    ap.add_argument("-o", "--out", default="measure/result-transport.json")
    a = ap.parse_args()

    truth = [len(w) for w in a.sentence.split()]
    rows = {}
    for form in CANDIDATES:
        enc = _encode(form, a.sentence)
        rows[form] = {}
        for name, fn in MEDIA.items():
            try:
                received = fn(enc)
            except Exception as e:
                rows[form][name] = {"verdict": "na", "why": f"{type(e).__name__}: {e}"}
                continue
            verdict, got = classify(form, truth, received)
            rows[form][name] = {"verdict": verdict, "lengths": got}

    result = {"sentence": a.sentence, "lengths": truth,
              "browser": BROWSER or "absent — every html/markdown row is na, not a pass",
              "forms": rows,
              "provenance": INSTRUMENT.block(sys.argv)}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(result, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    w = max(len(m) for m in MEDIA) + 2
    print(f'\n"{a.sentence}"  ->  {truth}\n')
    print(" " * w + "".join(f"{f:>21s}" for f in CANDIDATES))
    for name in MEDIA:
        line = f"{name:<{w}s}"
        for form in CANDIDATES:
            line += f"{rows[form][name]['verdict']:>21s}"
        print(line)
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
