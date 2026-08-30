#!/usr/bin/env python3
"""
constraints.py — one instrument, one unit, several constraints side by side.

ceiling.py answered "how much does a word's LENGTH carry" for one protocol. The same
machinery answers it for a whole family, and putting them in one table is what turns a
claim about Silent Language into a measurement about constrained writing generally.

Everything below is in ONE unit: BITS PER WORD, under the same unigram model on the same
corpus. Three columns, and keeping them apart is the entire point:

  WRITER PAYS       how much expressive freedom the constraint removes.
                    H(W) minus the entropy left over the admissible words.
  CHANNEL CARRIES   how much the transmitted skeleton says ABOUT THIS MESSAGE.
  READER SUPPLIES   what is left for the receiver to invent, given everything sent.

THE RESULT THE FAMILY EXISTS TO SHOW. Pilish and Snowball constrain word lengths exactly
as Silent Language does, and their writers pay exactly the same price per word. But their
skeleton is pi's digits, or 1,2,3,4... -- a PUBLIC CONSTANT, known before the text exists.
A constant carries no information, so the channel column is 0. Same sacrifice; one buys a
channel, the other buys nothing but the discipline itself.

That is the inversion stated numerically: Silent Language transmits ONLY the skeleton and
nothing else, where the Oulipo forms transmit everything else and never the skeleton.

WHAT IS AND IS NOT COMPARABLE HERE
  A lipogram removes a region of the VOCABULARY; a length rule removes everything but one
  slice of it. Both cost the writer bits and the costs are in the same unit, so they can
  sit in one column -- but "half a bit of lipogram" and "half a bit of length rule" are not
  the same experience, and the table says what each constraint is, not just what it costs.
  N+7 is in the table precisely because it costs ZERO: a bijection on the dictionary
  removes no freedom at all, which is worth seeing beside the ones that do.
"""

import argparse, json, math, os, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance import Instrument                      # noqa: E402
from ceiling import h_plugin, sentences_from, TOKENISERS  # noqa: E402

INSTRUMENT = Instrument(__file__)

# THE ALPHABET IS PART OF THE CONSTRAINT, and hardcoding a Latin one is the same mistake
# as running a Latin tokeniser over Cyrillic: the predicate does not FAIL, it quietly
# admits everything. Measured on Russian wikipedia with Latin predicates, a univocalism
# came out costing 0.12 bits and leaving 13.89 -- i.e. admitting essentially the whole
# vocabulary -- which reads as "Russian is barely constrained by a univocalism" and is
# absurd. A constraint that admits nearly everything is INAPPLICABLE, not cheap.
SCRIPTS = {
    "latin":    {"vowels": "aeiouy",      "lipograms": ("e", "t"), "univocal": "a"},
    "cyrillic": {"vowels": "аеёиоуыэюя",  "lipograms": ("о", "т"), "univocal": "а"},
}
# Above this share of tokens admitted, the constraint is not constraining and the row is
# refused rather than published as a small number.
INAPPLICABLE_ABOVE = 0.98


def detect_script(wc):
    """Which alphabet is this corpus in? Decided by token mass, not by a flag, so the
    caller cannot silently pick the wrong predicate set."""
    cyr = lat = 0
    for w, c in wc.items():
        for ch in w:
            if "\u0400" <= ch <= "\u04FF":
                cyr += c; break
            if ("a" <= ch <= "z") or ("A" <= ch <= "Z"):
                lat += c; break
    return "cyrillic" if cyr > lat else "latin"


def entropy_over(counts):
    return h_plugin(list(counts.values()))


def restricted(wc, predicate):
    """The sub-distribution the constraint admits, renormalised. Returns (entropy,
    token share retained, type share retained). A constraint that leaves NOTHING is
    reported as such rather than as zero entropy, because those are different facts."""
    sub = Counter({w: c for w, c in wc.items() if predicate(w)})
    tot = sum(wc.values())
    keep = sum(sub.values())
    if not keep:
        return None, 0.0, 0.0
    return entropy_over(sub), keep / tot, len(sub) / len(wc)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus-file", required=True)
    ap.add_argument("--tokeniser", default="stage_1", choices=list(TOKENISERS))
    ap.add_argument("--min-words", type=int, default=3)
    ap.add_argument("--max-words", type=int, default=12)
    ap.add_argument("-o", "--out", default="measure/result-constraints.json")
    a = ap.parse_args()

    rows = open(a.corpus_file, encoding="utf-8")
    wc = Counter()
    for _s, words in sentences_from(rows, a.min_words, a.max_words, a.tokeniser):
        for w in words:
            wc[w.lower()] += 1

    n = sum(wc.values())
    h_w = entropy_over(wc)

    # per-length conditional, token-weighted -- the same quantity ceiling.py publishes
    by_len = {}
    for w, c in wc.items():
        by_len.setdefault(len(w), Counter())[w] += c
    h_w_given_l = sum((sum(cc.values()) / n) * entropy_over(cc) for cc in by_len.values())
    h_l = entropy_over(Counter({L: sum(cc.values()) for L, cc in by_len.items()}))
    i_wl = h_w - h_w_given_l

    out = {"corpus": os.path.abspath(a.corpus_file), "tokeniser": a.tokeniser,
           "tokens": n, "types": len(wc),
           "H_word_bits": h_w, "H_length_bits": h_l,
           "H_word_given_length_bits": h_w_given_l, "I_word_length_bits": i_wl,
           "constraints": {}}

    def add(name, writer_pays, channel, reader, what, note, extra=None):
        row = {"writer_pays_bits_per_word": writer_pays,
               "channel_carries_bits_per_word": channel,
               "reader_supplies_bits_per_word": reader,
               "what_it_removes": what, "note": note}
        if extra:
            row.update(extra)
        out["constraints"][name] = row

    add("silent-language", i_wl, i_wl, h_w_given_l, "everything but one length slice",
        "The skeleton VARIES with the message and is the only thing transmitted. "
        "Writer's cost and channel capacity are the same number, which is what it means "
        "for the constraint to BE the message.")

    add("pilish", i_wl, 0.0, h_w_given_l, "everything but one length slice",
        "Identical per-word cost to silent-language: a word of an exactly required "
        "length. But the required lengths are pi's digits, a public constant known "
        "before the text exists, so the skeleton carries nothing about THIS text. Same "
        "sacrifice, no channel. (The digit 0 is conventionally a ten-letter word; that "
        "convention changes which lengths appear, never the fact that they are fixed.)")

    add("snowball", i_wl, 0.0, h_w_given_l, "everything but one length slice, ascending",
        "Cost per word is the same length rule; what differs is that the required "
        "length CLIMBS, and long words are rare. See per_position below: the writer's "
        "remaining freedom collapses with position, and the form ends where the corpus "
        "runs out of words.",
        {"per_position": {
            str(L): {"words_available": len(by_len.get(L, {})),
                     "token_share": sum(by_len[L].values()) / n if L in by_len else 0.0,
                     "writer_freedom_bits": entropy_over(by_len[L]) if L in by_len else None}
            for L in range(1, 21)}})

    script = detect_script(wc)
    sc = SCRIPTS[script]
    out["script"] = script
    cases = [(f"lipogram-no-{L}", (lambda x: (lambda w: x not in w))(L),
              f"every word containing {L!r}") for L in sc["lipograms"]]
    uv = sc["univocal"]
    cases.append((f"univocalic-{uv}",
                  (lambda vs, u: (lambda w: set(w) & vs <= {u}))(set(sc["vowels"]), uv),
                  f"every word whose vowels are not only {uv!r}"))
    for label, pred, what in cases:
        h_sub, tok_share, type_share = restricted(wc, pred)
        if h_sub is None:
            add(label, None, 0.0, None, what, "the constraint admits no word in this corpus")
            continue
        if tok_share > INAPPLICABLE_ABOVE:
            add(label, None, 0.0, None, what,
                f"INAPPLICABLE to this corpus: the predicate admits {100*tok_share:.1f}% of "
                f"tokens, so it is not constraining anything. Almost always this means the "
                f"predicate is written in the wrong alphabet for the corpus (script "
                f"detected: {script}). A near-zero cost here would be an artifact, not a "
                f"cheap constraint.",
                {"token_share_admissible": tok_share, "type_share_admissible": type_share})
            continue
        add(label, h_w - h_sub, 0.0, h_sub, what,
            "Removes a REGION of the vocabulary rather than all but a slice. The "
            "constraint is public, and the text is transmitted in full, so it carries "
            "nothing about the message either.",
            {"token_share_admissible": tok_share, "type_share_admissible": type_share})

    add("n-plus-7", 0.0, 0.0, h_w, "nothing",
        "A dictionary shift is a BIJECTION, so it removes no freedom and destroys no "
        "entropy: the same distribution wearing different labels. It is in this table to "
        "mark the zero, and because being told a transformation costs nothing is worth a "
        "row.")

    out["provenance"] = INSTRUMENT.block(sys.argv)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print(f"\ncorpus {os.path.basename(a.corpus_file)}  tokeniser {a.tokeniser}  "
          f"{n} tokens, {len(wc)} types")
    print(f"H(word) {h_w:.3f}   H(length) {h_l:.3f}   H(word|length) {h_w_given_l:.3f}\n")
    print(f"{'constraint':<18}{'writer pays':>13}{'channel':>10}{'reader supplies':>18}")
    for k, v in out["constraints"].items():
        wp = v["writer_pays_bits_per_word"]; rs = v["reader_supplies_bits_per_word"]
        print(f"{k:<18}{('n/a' if wp is None else f'{wp:.3f}'):>13}"
              f"{v['channel_carries_bits_per_word']:>10.3f}"
              f"{('n/a' if rs is None else f'{rs:.3f}'):>18}")
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
