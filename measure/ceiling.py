#!/usr/bin/env python3
"""
ceiling.py — how much can the length channel carry AT ALL?

silent_channel.py asked whether readers recover the message and answered no: against
a prior control, neither message showed recovery. That is a result about two messages,
one reader family and one framing. This asks the question underneath it, and it needs
no model at all:

    a word's shape is its LENGTH. How many bits is that, against how many bits a word
    carries?

If the answer is "a small fraction", then the null result is not a failure of the
readers. It is the prediction. And a training lane (stage_1/) that reports only
"it worked / it did not" is measuring against the wrong target: the target is the
CEILING, and the interesting number is how close a model gets to it.

THREE ARMS, in increasing order of how much they assume.

  1. CAPACITY (assumes nothing but the corpus)
     H(L), the entropy of a single word's length. This is a hard ceiling on the
     channel: whatever a reader recovers about a word, it arrives through L, so it
     cannot exceed H(L) bits per word. Support is ~20 values with millions of
     samples, so this estimate is tight.

  2. WHAT THE SHAPE TELLS YOU ABOUT THE WORD (assumes a unigram model)
     I(W;L) = H(W) - H(W|L), and the residual H(W|L) is what the READER must supply.
     Both terms under the same unigram model, so the ratio is comparable.

     A correction this arm was BUILT ON A WRONG PREMISE, kept here because the
     mistake is instructive. It was written expecting the plug-in estimator to
     inflate I -- "biased down, and biased down harder on the conditional, because
     each length bin holds fewer samples". Under Miller-Madow that is exactly
     backwards, and the test that asserts the direction is what caught it. Every
     word has exactly one length, so the observed word types partition across the
     bins: the conditional's total correction is (K-L)/(2N), the marginal's is
     (K-1)/(2N), and therefore

         I_plugin = I_MillerMadow - (L-1)/(2N ln2)

     -- the plug-in UNDERSTATES I. At this corpus's own N and L (6.89e6 tokens, 32
     distinct lengths) that term is 3.2e-6 bits, and it matches the artifact to eleven
     digits. An earlier draft of this paragraph put it ten orders of magnitude lower --
     the figure is deliberately NOT repeated here, because the gate that now pins this
     value is a source-text check and a retraction that quotes its own retracted literal
     re-arms the thing it retracts. Nothing had ever checked the stated size: the test
     asserted only that the term is small, which a decorative claim satisfies as easily
     as a true one. It is still far too small to matter, but a number nobody can be
     wrong about is a number nobody is measuring.

     Where it does live: Miller-Madow keys on OBSERVED types, and a word
     distribution's mass sits in types this corpus never saw. Both entropies are
     underestimated by an unknown amount that the correction cannot see, and the
     conditional's bins are smaller, so its unseen mass is proportionally larger.
     The direction of the RATIO's bias is therefore genuinely unknown, and no
     first-order correction settles it. What can be checked is CONVERGENCE, so the
     same estimate is recomputed on a random half of the tokens and both are
     reported: an estimate still moving between N/2 and N is not converged, whatever
     its correction says. H(L) has none of this trouble -- ~20 values, millions of
     samples -- which is why arm 1 and not arm 2 carries the headline.

  3. COLLISIONS (assumes nothing, but only ever gives a LOWER bound)
     How many DISTINCT corpus sentences share one exact length signature. A signature
     seen once in this corpus is not thereby unique in English, so the in-corpus
     count understates ambiguity. That understatement is not argued, it is MEASURED:
     the same computation is run at 10%, 25%, 50% and 100% of the corpus, and the
     unique-signature fraction is reported at each. If uniqueness is a sampling
     artifact it falls as the corpus grows -- and a reader can watch it fall.

  So arm 2 bounds the channel from above and arm 3 from below, and they are wrong in
  opposite directions on purpose. Arm 2's candidate count assumes positions are
  independent, which real syntax is not, so it OVERSTATES how many sentences fit a
  shape. Arm 3 counts only what the corpus happened to contain, so it UNDERSTATES.

TOKENISATION IS PART OF THE CHANNEL, so both live here.
  silent_channel.py splits words with [A-Za-z']+ and stage_1/ with \\b\\w+\\b. Those
  are different channels: "don't" is one 5-shape under the first and two shapes (3,1)
  under the second. Every number is reported per tokeniser rather than picking one.
"""

import argparse, json, math, os, random, re, sys, hashlib
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from provenance import Instrument

INSTRUMENT = Instrument(__file__)

LN2 = math.log(2.0)

TOKENISERS = {
    # the instrument in measure/: an apostrophe is part of the word
    "measure": re.compile(r"[A-Za-z']+"),
    # the instrument in stage_1/: \w splits on the apostrophe
    "stage_1": re.compile(r"\b\w+\b"),
}


# --------------------------------------------------------------- estimators
def h_plugin(counts):
    """Maximum-likelihood (plug-in) entropy in bits. Biased DOWN: unseen types
    contribute nothing, so the distribution looks more concentrated than it is."""
    n = sum(counts)
    if n == 0:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in counts if c)


def h_miller_madow(counts):
    """Plug-in plus (K-1)/(2N) nats, K = number of OBSERVED types. The standard
    first-order correction for the plug-in's downward bias. It is a correction, not
    a cure: K is what was SEEN, and on a heavy tail most of the types were not, so
    this still underestimates -- and by more, not less, in a small bin."""
    n = sum(counts)
    if n == 0:
        return 0.0
    k = sum(1 for c in counts if c)
    return h_plugin(counts) + (k - 1) / (2.0 * n * LN2)


def conditional_entropy(joint):
    """H(W|L) from {length: Counter(word)}. Each bin is corrected SEPARATELY,
    because the bias is a property of the bin's own sample size. The corrections then
    sum to (K-L)/(2N) nats rather than (K-1)/(2N) -- see the note in the module
    docstring, which is where that arithmetic stopped being a guess."""
    total = sum(sum(c.values()) for c in joint.values())
    hp = hmm = 0.0
    for _l, c in joint.items():
        n_l = sum(c.values())
        w = n_l / total
        vals = list(c.values())
        hp += w * h_plugin(vals)
        hmm += w * h_miller_madow(vals)
    return hp, hmm


# --------------------------------------------------------------- corpus
SENT_SPLIT = re.compile(r"(?<=[.!?]) +")


def sentences_from(rows, min_words, max_words, tokeniser):
    """Same shape as stage_1/auto_dataset_creation.py: split on sentence enders, drop
    wikitext heading lines, keep sentences inside the word-count window."""
    wre = TOKENISERS[tokeniser]
    for text in rows:
        for s in SENT_SPLIT.split(text):
            s = s.strip()
            if not s or "=" in s:
                continue
            words = wre.findall(s)
            if min_words <= len(words) <= max_words:
                yield s, words


def load_rows(args):
    if args.corpus_file:
        with open(args.corpus_file, encoding="utf-8") as f:
            rows = [l for l in f]
        source = {"kind": "file", "path": os.path.abspath(args.corpus_file),
                  "rows": len(rows)}
        return rows, source
    from datasets import load_dataset
    d = load_dataset(args.hf_dataset, args.hf_config, split=args.hf_split)
    rows = d["text"]
    if args.max_rows:
        rows = rows[: args.max_rows]
    source = {"kind": "huggingface", "dataset": args.hf_dataset,
              "config": args.hf_config, "split": args.hf_split,
              "rows_available": len(d), "rows_used": len(rows)}
    return rows, source


# --------------------------------------------------------------- arms
def arm_capacity_and_word(words):
    """Arms 1 and 2, from a flat iterable of words OR an already-built Counter.

    The Counter form is not an optimisation detail: wikitext-103 is ~10^8 tokens, and
    materialising that as a list of str costs more memory than the machine has. The
    caller streams."""
    wc = words if isinstance(words, Counter) else Counter(words)
    # TOKEN-weighted, and it must be built from wc.items(). `Counter(len(w) for w in
    # words)` iterates a Counter's KEYS, so on the only path main() ever takes it counted
    # each word TYPE once and H(L) became the entropy of a type inventory instead of the
    # entropy of running text. It inflated the headline by 0.12 bits, and the artifact
    # said so all along: length_distribution summed to 198,898 (the type count) and not
    # to 6,885,209 (the tokens).
    lc = Counter()
    for _w, _c in wc.items():
        lc[len(_w)] += _c
    joint = defaultdict(Counter)
    for w, c in wc.items():
        joint[len(w)][w] += c

    hw_p, hw_m = h_plugin(list(wc.values())), h_miller_madow(list(wc.values()))
    hl_p, hl_m = h_plugin(list(lc.values())), h_miller_madow(list(lc.values()))
    hwl_p, hwl_m = conditional_entropy(joint)

    return {
        "tokens": sum(wc.values()),
        "word_types": len(wc),
        "length_values": len(lc),
        "H_word_bits": {"plugin": hw_p, "miller_madow": hw_m},
        "H_length_bits": {"plugin": hl_p, "miller_madow": hl_m},
        "H_word_given_length_bits": {"plugin": hwl_p, "miller_madow": hwl_m},
        "I_word_length_bits": {"plugin": hw_p - hwl_p, "miller_madow": hw_m - hwl_m},
        # H(L|W) = 0 -- every word has exactly one length -- so I(W;L) == H(L) is an
        # IDENTITY, not a bound. Publishing the residual makes any future population
        # mismatch between the two estimates visible in the artifact instead of hiding
        # inside an inequality that a bug can satisfy.
        "identity_residual_bits": {"plugin": (hw_p - hwl_p) - hl_p,
                                   "miller_madow": (hw_m - hwl_m) - hl_m},
        "shape_share_of_word": {
            "plugin": (hw_p - hwl_p) / hw_p if hw_p else 0.0,
            "miller_madow": (hw_m - hwl_m) / hw_m if hw_m else 0.0,
        },
        "effective_words_per_slot": {
            "plugin": 2 ** hwl_p, "miller_madow": 2 ** hwl_m,
        },
        "length_distribution": dict(sorted(lc.items())),
    }


def arm_collisions(signatures, fractions, seed):
    """Arm 3. `signatures` is one signature per DISTINCT sentence text (the caller
    dedupes; a corpus that repeats a sentence must not make its shape look busier).
    Recomputed on nested random subsamples so the finite-sample nature of
    'this signature is unique' is measured rather than asserted."""
    rng = random.Random(seed)
    order = list(range(len(signatures)))
    rng.shuffle(order)
    out = []
    for frac in fractions:
        k = max(1, int(len(order) * frac))
        groups = Counter(signatures[i] for i in order[:k])
        sizes = sorted(groups.values())
        n_sigs = len(sizes)
        uniq = sum(1 for s in sizes if s == 1)
        # sentence-weighted: for a sentence drawn at random, how many others share
        # its shape? That is the number a reader actually faces.
        weighted = sum(s * s for s in sizes) / k
        out.append({
            "fraction": frac,
            "distinct_sentences": k,
            "distinct_signatures": n_sigs,
            "unique_signature_share_of_signatures": uniq / n_sigs if n_sigs else 0.0,
            "unique_signature_share_of_sentences": uniq / k,
            "median_group_size": sizes[len(sizes) // 2] if sizes else 0,
            "max_group_size": sizes[-1] if sizes else 0,
            "mean_group_size_a_sentence_lands_in": weighted,
        })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hf-dataset", default="Salesforce/wikitext")
    ap.add_argument("--hf-config", default="wikitext-103-raw-v1")
    ap.add_argument("--hf-split", default="train")
    ap.add_argument("--corpus-file", default=None,
                    help="plain text, one document per line; skips huggingface entirely")
    ap.add_argument("--max-rows", type=int, default=0)
    ap.add_argument("--min-words", type=int, default=3)
    ap.add_argument("--max-words", type=int, default=12)
    ap.add_argument("--seed", type=int, default=20260830)
    ap.add_argument("--tokenisers", default=",".join(TOKENISERS),
                    help="comma-separated subset of " + ",".join(TOKENISERS) +
                         ". A CROSS-LANGUAGE comparison must pin ONE of them: 'measure' is "
                         "[A-Za-z']+ and matches nothing at all in Cyrillic, so running the "
                         "default pair on a Russian corpus would silently report an empty "
                         "arm beside a real one.")
    ap.add_argument("-o", "--out", default="measure/result-ceiling.json")
    a = ap.parse_args()

    rows, source = load_rows(a)

    result = {"corpus": source, "window": [a.min_words, a.max_words], "seed": a.seed,
              "tokenisers": {}}

    _toks = [t.strip() for t in a.tokenisers.split(",") if t.strip()]
    for t in _toks:
        if t not in TOKENISERS:
            raise SystemExit(f"unknown tokeniser {t!r}; known: {', '.join(TOKENISERS)}")
    for tok in _toks:
        full = Counter()
        # convergence arm: an independent coin per TOKEN OCCURRENCE, not per type --
        # sampling types would keep every type and only shrink counts, which is not
        # a smaller corpus, it is the same corpus rescaled.
        half = Counter()
        rng = random.Random(a.seed)
        sigs = []
        seen = set()
        for sent, words in sentences_from(rows, a.min_words, a.max_words, tok):
            for w in words:
                full[w] += 1
                if rng.random() < 0.5:
                    half[w] += 1
            h = hashlib.blake2b(sent.encode("utf-8"), digest_size=16).digest()
            if h in seen:
                continue
            seen.add(h)
            sigs.append(tuple(len(w) for w in words))
        del seen

        if not full:
            raise SystemExit(
                f"tokeniser {tok!r} matched ZERO tokens in this corpus. That is not a "
                f"result, it is the wrong instrument: 'measure' is [A-Za-z']+ and cannot "
                f"see Cyrillic. Pick one with --tokenisers.")
        word_arm = arm_capacity_and_word(full)
        half_arm = arm_capacity_and_word(half)

        coll = arm_collisions(sigs, [0.10, 0.25, 0.50, 1.00], a.seed)

        by_n = {}
        for n in range(a.min_words, a.max_words + 1):
            sub = [s for s in sigs if len(s) == n]
            if len(sub) < 100:
                continue
            g = Counter(sub)
            sizes = sorted(g.values())
            by_n[n] = {
                "distinct_sentences": len(sub),
                "distinct_signatures": len(g),
                "unique_signature_share_of_sentences": sum(1 for x in sizes if x == 1) / len(sub),
                "mean_group_size_a_sentence_lands_in": sum(x * x for x in sizes) / len(sub),
                "shape_bits_ceiling": n * word_arm["H_length_bits"]["miller_madow"],
                "word_bits_needed_unigram": n * word_arm["H_word_bits"]["miller_madow"],
            }

        result["tokenisers"][tok] = {
            "distinct_sentences": len(sigs),
            "word_arm_full": word_arm,
            "word_arm_half": {
                "tokens": half_arm["tokens"],
                "I_word_length_bits": half_arm["I_word_length_bits"],
                "H_word_given_length_bits": half_arm["H_word_given_length_bits"],
            },
            "collisions_by_corpus_fraction": coll,
            "by_sentence_length": by_n,
        }

    result["provenance"] = INSTRUMENT.block(sys.argv, corpus=source)

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, ensure_ascii=False)

    for tok, r in result["tokenisers"].items():
        w = r["word_arm_full"]
        print(f"\n=== tokeniser {tok}  ({w['tokens']} tokens, {w['word_types']} types, "
              f"{r['distinct_sentences']} distinct sentences) ===")
        print(f"  H(length)                 {w['H_length_bits']['miller_madow']:.3f} bits"
              "   <- hard ceiling on the channel, per word")
        print(f"  H(word)                   {w['H_word_bits']['miller_madow']:.3f} bits")
        print(f"  H(word | length)          {w['H_word_given_length_bits']['miller_madow']:.3f} bits"
              "   <- the reader supplies this")
        print(f"  I(word; length)           {w['I_word_length_bits']['miller_madow']:.3f} bits"
              f"   = {100*w['shape_share_of_word']['miller_madow']:.1f}% of the word")
        print(f"  effective words per slot  {w['effective_words_per_slot']['miller_madow']:.0f}")
        hi = r["word_arm_half"]["I_word_length_bits"]["miller_madow"]
        print(f"  convergence: I on a random half = {hi:.3f} bits "
              f"(full {w['I_word_length_bits']['miller_madow']:.3f}, "
              f"delta {abs(hi - w['I_word_length_bits']['miller_madow']):.3f})")
        print("  unique-signature share of sentences, by corpus fraction:")
        for c in r["collisions_by_corpus_fraction"]:
            print(f"    {int(c['fraction']*100):3d}%  n={c['distinct_sentences']:>9d}  "
                  f"unique {100*c['unique_signature_share_of_sentences']:.2f}%   "
                  f"a sentence lands in a group of {c['mean_group_size_a_sentence_lands_in']:.1f}")
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
