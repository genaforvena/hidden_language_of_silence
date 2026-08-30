#!/usr/bin/env python3
"""
silent_channel.py — does the Silent Language channel carry recoverable signal?

The README of this repository asserts, without measurement, that LLM readers
"never recover intended meaning". That is a testable claim, and it has never been
tested. This is the test.

WHAT THE CHANNEL ACTUALLY CARRIES
  Encoding maps a sentence to one symbol cluster per word, cluster length = word
  length, symbol choice explicitly meaningless. So the entire channel is the
  LENGTH SEQUENCE L = [l1..ln]. Nothing else survives encoding. Any signal a
  reader recovers must come from L (plus the reader's own prior).

THE MEASUREMENT
  Encode a known text, take N INDEPENDENT readings, and measure how much the
  readings agree WITH EACH OTHER — against an explicit random basis at THE SAME
  LENGTHS AND THE SAME ALPHABET. Without that matched basis you are measuring the
  model's prior, not the channel.

  Arm A  TREATMENT      N readings conditioned on the true message's L.
  Arm B  PRIOR CONTROL  N readings conditioned on L' — a DIFFERENT length sequence,
                        same word count, lengths resampled from the same length
                        distribution. Whatever agreement appears here is what the
                        task framing and the model's prior produce on their own,
                        with no particular message behind it.
  Arm C  RANDOM BASIS   N texts assembled with NO model: at each position draw a
                        random word of exactly that length from a lexicon pooled
                        out of arm B's own readings. Same lengths as A, same
                        alphabet as the model, zero conditioning and zero local
                        coherence. This is the chance floor.

  The lexicon is pooled from arm B and not from arm A on purpose: pooling it from
  A would let A's own convergence raise its floor and hide the effect.

  RECOVERY is asked separately from CONVERGENCE, because they are different
  claims. Recovery compares each arm-A reading to the TRUE original against
  DECOY originals carrying the same length profile — if readings are no closer to
  the truth than to a matched decoy, the channel carries no recoverable meaning
  however much the readings agree with each other.

READING THE RESULT
  A > C  the readings converge above the random floor: the channel + reader carry
         convergent structure. Compare A against B to see whether it is THIS
         message doing it or merely the shape of the task.
  A ~ C  the claim in the README is, for the first time, supported by a
         measurement rather than asserted.
  Both outcomes are publishable. A negative result here is a real result.

Everything the run produces — every reading, every arm, every pair — is written to
the JSON artifact, so the numbers can be recomputed without re-running the models.
"""

import argparse, datetime, hashlib, json, os, random, re, subprocess, sys, urllib.request
from statistics import mean

WORD_RE = re.compile(r"[A-Za-z']+")
OLLAMA = os.environ.get("SILENT_OLLAMA", "http://127.0.0.1:11434")
EMBED_MODEL = os.environ.get("SILENT_EMBED_MODEL", "all-minilm")
# FROZEN. The docs and the demo moved off Dingbats (U+27xx) and U+25FC because Android
# draws those from the emoji font, at double width, which swallows the space between
# clusters. This alphabet is deliberately NOT updated to match: these are the exact
# glyphs that were sent to the models in the runs stored beside this file. Changing them
# would leave the tree describing an instrument that produced none of the artifacts --
# the failure the provenance block below exists to catch. Change it only together with a
# re-run, and the script_sha256 stamp will correctly mark the artifacts as older.
SYMBOLS = "◆✦➤✿✶✪✧◼✖▲●■◇☙❖⬟⬢⧫"


# ------------------------------------------------------------- provenance
# A result file that cannot name the instrument that wrote it is not evidence.
#
# This is not hypothetical here. measure/result-msg2.json — the replication that
# REVERSES the headline of run 1 — was written 03:28:14Z by a process launched
# before the 03:24:31Z commit that added by_position(). Python reads its source
# once, at start, so that run executed the OLD code to completion and produced
# output from an instrument that no longer exists in the tree. The only trace was
# a MISSING KEY, which reads exactly like a run that had nothing to report.
#
# So the stamp is taken TWICE and both halves are kept:
#
#   at_start  is what actually ran. Taken at import, before main() does anything,
#             because the tree can move under a run that takes twenty minutes —
#             and in the case above it did. A stamp taken only at WRITE time would
#             have recorded 50bac6b for msg2: the commit that was NOT running.
#   at_write  is the tree as it stands when the artifact lands.
#
# When they disagree, `changed_mid_run` says so IN the file. That converts the
# weakest possible signal (an absent key) into a positive assertion, which is the
# whole point: absence and "nothing to report" must not render identically.
#
# Every field fails to a string beginning "unknown:" that names which probe failed.
# A provenance field that quietly reports a plausible default is worse than none.

SCRIPT = os.path.abspath(__file__)


def _git(*args):
    try:
        p = subprocess.run(["git", "-C", os.path.dirname(SCRIPT)] + list(args),
                           capture_output=True, text=True, timeout=15)
        return p.stdout.strip() if p.returncode == 0 else None
    except Exception:
        return None


def _script_sha():
    """sha256 of the source on disk. Read as early as possible: the interpreter has
    already loaded and compiled these bytes, so at import time this is what is
    running. Read it at write time instead and you hash whatever the file became."""
    try:
        with open(SCRIPT, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return "unknown:script-unreadable"


def stamp():
    head = _git("rev-parse", "HEAD")
    inst = _git("status", "--porcelain", "--", SCRIPT)
    tree = _git("status", "--porcelain")
    return {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "script_sha256": _script_sha(),
        "git_head": head or "unknown:not-a-repo-or-git-failed",
        "instrument_dirty": None if inst is None else bool(inst.strip()),
        "tree_dirty_files": None if tree is None else len([l for l in tree.splitlines() if l.strip()]),
    }


PROVENANCE_AT_START = stamp()


def provenance(argv, relay, embed_model, used_embed):
    """The block written into every artifact. Compares the start stamp against a
    fresh one so a mid-run edit of the instrument is ASSERTED, not merely absent."""
    now = stamp()
    # The verdict keys on the INSTRUMENT'S OWN BYTES, never on git_head. HEAD is a
    # property of the TREE: any commit anywhere in the repo moves it, and on a run
    # that takes hours that is a near-certainty. Keyed on HEAD this field would be
    # permanently true, therefore permanently ignored, and a REAL instrument change
    # would ride in under exactly that suppression.
    #
    # Measured here, not reasoned about: the two runs of 2026-08-30 were launched at
    # 21f344b, and committing the TEST FILE mid-run moved HEAD to 79594e1 while
    # `git rev-parse 21f344b:measure/silent_channel.py` and `79594e1:...` are the
    # same blob a1c4c8a8. The first version of this function called that "the
    # instrument changed under this run", which was false.
    changed = [k for k in ("script_sha256", "instrument_dirty")
               if PROVENANCE_AT_START.get(k) != now.get(k)]
    tree_moved = PROVENANCE_AT_START.get("git_head") != now.get("git_head")
    return {
        "at_start": PROVENANCE_AT_START,
        "at_write": now,
        "changed_mid_run": changed or False,
        "tree_moved_mid_run": tree_moved,   # context, never the alarm
        "note": ("the instrument changed under this run — at_start is what produced "
                 "these numbers" if changed else
                 "instrument identical at start and at write"
                 + (" (HEAD moved, but the instrument's own bytes did not)"
                    if tree_moved else "")),
        "argv": list(argv),
        "relay": relay,
        "embed_model": embed_model if used_embed else None,
        "python": sys.version.split()[0],
    }


# ---------------------------------------------------------------- the protocol
def words_of(text):
    return WORD_RE.findall(text)


def lengths_of(text):
    return [len(w) for w in words_of(text)]


def encode(text, rng):
    """The repo's protocol: one freely chosen symbol per word, repeated word-length
    times. Symbol choice carries no message, so it is drawn fresh every time."""
    return " ".join(rng.choice(SYMBOLS) * n for n in lengths_of(text))


def profile_matches(text, lens):
    return lengths_of(text) == list(lens)


# ---------------------------------------------------------------- the reader
PROMPT = """You are reading a message written in Silent Language.

Each cluster of repeated symbols stands for exactly one word. The NUMBER of symbols
in a cluster is the LENGTH of that word. The symbols themselves are arbitrary and
carry no meaning whatsoever.

Message:
{encoded}

Word lengths, in order: {lens}

Write the one sentence you read here. It must have exactly {n} words, and the
word lengths must be exactly {lens} in that order. Reply with the sentence alone —
no quotes, no explanation, no preamble."""


def read_once(lens, rng, tries=4, relay=None):
    """One INDEPENDENT reading. Each call is its own process with no shared context,
    which is what makes the N readings independent rather than a single sampled list.
    Returns (text, attempts) or (None, attempts) if the reader never hit the profile."""
    encoded = " ".join(rng.choice(SYMBOLS) * n for n in lens)
    prompt = PROMPT.format(encoded=encoded, lens=" ".join(map(str, lens)), n=len(lens))
    for attempt in range(1, tries + 1):
        try:
            out = subprocess.run([relay or "mesh-relay", prompt], capture_output=True,
                                 text=True, timeout=120).stdout.strip()
        except subprocess.TimeoutExpired:
            continue
        for line in [l.strip() for l in out.splitlines() if l.strip()]:
            cand = line.strip().strip('"').strip("'")
            if profile_matches(cand, lens):
                return cand, attempt
    return None, tries


# ---------------------------------------------------------------- the arms
def resample_lengths(lens, rng):
    """A DIFFERENT length sequence with the same word count, drawn from the same
    length distribution. Rejects an accidental copy of the original."""
    for _ in range(64):
        alt = [rng.choice(lens) for _ in lens]
        if alt != list(lens):
            return alt
    return list(reversed(lens))


def random_basis(lens, lexicon, rng, n_texts):
    """Arm C: same lengths, same alphabet, no model and no coherence. A position
    whose length appears nowhere in the lexicon is left as None so the pair metric
    can skip it honestly instead of substituting a word of the wrong length."""
    out = []
    for _ in range(n_texts):
        out.append([rng.choice(lexicon[l]) if lexicon.get(l) else None for l in lens])
    return out


def pool_lexicon(texts):
    lex = {}
    for t in texts:
        for w in words_of(t.lower()):
            lex.setdefault(len(w), set()).add(w)
    return {k: sorted(v) for k, v in lex.items()}


def merge_lexicons(*lexes):
    out = {}
    for lex in lexes:
        for k, v in lex.items():
            out.setdefault(k, set()).update(v)
    return {k: sorted(v) for k, v in out.items()}


def vocabulary_pool(rng, relay, want=240):
    """The alphabet for the random basis, drawn from the READER'S OWN vocabulary but
    conditioned on NO message and NO length sequence.

    Pooling the basis out of the control arm's few readings — the first version of
    this — is not a floor. Seven texts yield a vocabulary so small that the random
    texts built from it are near-duplicates of each other, which inflates every
    agreement metric and inflates the SEMANTIC one worst (measured: cosine 0.391 for
    a basis pooled from 7 texts, ABOVE the model readings it was supposed to sit
    under). A floor that rises with how little you sampled it is not a floor.

    Requesting a plain word list instead keeps the alphabet the model's own while
    making it message-independent and large. Returns {} if the reader will not
    produce one, and the caller then falls back and SAYS it fell back."""
    prompt = (f"List {want} common English words, one per line, nothing else. "
              "Mix lengths from 1 to 12 letters. No numbering, no punctuation.")
    try:
        out = subprocess.run([relay, prompt], capture_output=True, text=True,
                             timeout=180).stdout
    except subprocess.TimeoutExpired:
        return {}
    words = [w.lower() for w in WORD_RE.findall(out)]
    lex = {}
    for w in words:
        lex.setdefault(len(w), set()).add(w)
    return {k: sorted(v) for k, v in lex.items()}


# ---------------------------------------------------------------- the metrics
def positional_agreement(a, b):
    """Fraction of positions where two texts choose the SAME word. Meaningful only
    between texts sharing a length profile — which every text inside one arm does."""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if not pairs:
        return None
    return sum(1 for x, y in pairs if x == y) / len(pairs)


def jaccard(a, b):
    sa, sb = {w for w in a if w}, {w for w in b if w}
    if not sa or not sb:
        return None
    return len(sa & sb) / len(sa | sb)


def embed(text):
    req = urllib.request.Request(
        f"{OLLAMA}/api/embeddings",
        data=json.dumps({"model": EMBED_MODEL, "prompt": text}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r).get("embedding")


def cosine(u, v):
    if not u or not v:
        return None
    du = sum(x * x for x in u) ** 0.5
    dv = sum(x * x for x in v) ** 0.5
    if du == 0 or dv == 0:
        return None
    return sum(x * y for x, y in zip(u, v)) / (du * dv)


def pairwise(vals, fn):
    out = []
    for i in range(len(vals)):
        for j in range(i + 1, len(vals)):
            s = fn(vals[i], vals[j])
            if s is not None:
                out.append(s)
    return out


def boot_ci(xs, rng, iters=2000, alpha=0.05):
    """Bootstrap CI. Pairwise similarities are NOT independent (they share texts),
    so this is a descriptive interval on the mean, not a significance test — the
    comparison that carries the argument is arm-vs-arm on the same construction."""
    if not xs:
        return (None, None)
    n = len(xs)
    means = sorted(mean(rng.choice(xs) for _ in range(n)) for _ in range(iters))
    return (means[int(iters * alpha / 2)], means[int(iters * (1 - alpha / 2))])


def boot_diff_ci(xs, ys, rng, iters=20000, alpha=0.05):
    """Interval on mean(xs) - mean(ys) for two INDEPENDENT arms.

    Unlike boot_ci above, this one does carry an argument: arm A and arm B are
    separate readings by separate processes of two different length sequences, so
    resampling each arm on its own is legitimate. An interval containing 0 says the
    treatment arm is no closer to the message than an arm that never saw it."""
    if not xs or not ys:
        return (None, None)
    ds = sorted(mean(rng.choice(xs) for _ in range(len(xs)))
                - mean(rng.choice(ys) for _ in range(len(ys)))
                for _ in range(iters))
    return (ds[int(iters * alpha / 2)], ds[int(iters * (1 - alpha / 2))])


def recovery_block(message, A, B, C_texts, lens, lex, rng, embed_fn=None):
    """The RECOVERY arm, as ONE entry point.

    It lives here rather than at each call site because there were two copies — the
    inline run and the post-hoc recompute — and they had already drifted: the
    recompute shipped bare means with no interval at all.

    THE FLOOR THIS ARM IS MEASURED AGAINST WAS THE WRONG ONE, and it was wrong in
    the direction that manufactures a result. The original arm compared arm-A
    readings to the true message against **length-matched decoys**, which is a
    CHANCE floor: measured on `result-msg1-stamped.json` the decoy floor is 0.153
    and the model-free arm C sits at 0.159, the same number. But arm B — real
    readings, by the same model, under the same framing, of a DIFFERENT length
    sequence — sits at 0.220. A reading can beat random word salad purely because
    it is fluent English about a plausible scene, having recovered nothing.

    So the verdict keys on **A - B**, and the decoy and arm-C floors are kept as
    context rather than as the test. This is the repository's own headline lesson
    about the convergence arm ("agreement above chance requires the chance arm to
    share the lengths AND the alphabet") applied one ring out: the convergence arm
    always had both a prior control and a chance basis, and the recovery arm beside
    it had only the chance basis."""
    e = embed_fn or embed
    v_true = e(message)
    decoys = [" ".join(rng.choice(lex[l]) if lex.get(l) else "x" * l for l in lens)
              for _ in range(8)]
    v_dec = [e(x) for x in decoys]

    def against_true(texts):
        return [c for c in (cosine(e(t), v_true) for t in texts) if c is not None]

    to_true, to_prior, to_chance = against_true(A), against_true(B), against_true(C_texts)
    to_decoy = []
    for t in A:
        v = e(t)
        ds = [x for x in (cosine(v, w) for w in v_dec) if x is not None]
        if ds:
            to_decoy.append(mean(ds))

    def arm(xs):
        return {"mean": mean(xs) if xs else None, "ci": boot_ci(xs, rng), "n": len(xs)}

    d_prior = boot_diff_ci(to_true, to_prior, rng)
    d_chance = boot_diff_ci(to_true, to_chance, rng)

    # An arm with no readings is BLINDNESS, and it must not wear a verdict. Found by
    # the first live drive of this code: at n=6 the reader missed the length profile
    # on all six control readings, so to_prior was n=0 — and the block still said
    # "NO recovery above the prior (A - B_prior includes 0)", which is a claim about
    # an interval that does not exist. The failure direction is the bad one: no
    # recovery is also the true answer, so a blind run agrees with the real ones and
    # is indistinguishable from them. `excludes_zero` is None, never False, for the
    # same reason — False is a measured negative.
    if not to_true or not to_prior:
        missing = [n for n, xs in (("A_treatment", to_true), ("B_prior", to_prior)) if not xs]
        verdict = ("UNKNOWN — no verdict is possible: "
                   + " and ".join(missing) + " has no valid readings")
        beats = None
    else:
        beats = (d_prior[0] is not None and d_prior[0] > 0)
        verdict = ("recovered above the prior" if beats else
                   "NO recovery above the prior (A - B_prior includes 0)")

    return {
        "metric": "cosine_similarity",
        "direction": "higher = closer to the target",
        "reading": ("RECOVERY is A minus B_prior. to_decoy and to_chance are floors for "
                    "context, not the test: a length-matched decoy is a CHANCE floor, and "
                    "beating it only says the reading is fluent English rather than word "
                    "salad. B_prior is real readings of a DIFFERENT length sequence by the "
                    "same model under the same framing — the prior with no channel behind "
                    "it. If A - B_prior includes 0, nothing was recovered."),
        "verdict": verdict,
        "to_true":   arm(to_true),
        "to_prior":  arm(to_prior),
        "to_chance": arm(to_chance),
        "to_decoy":  arm(to_decoy),
        "A_minus_prior":  {"delta": (mean(to_true) - mean(to_prior)) if to_true and to_prior else None,
                           "ci": d_prior, "excludes_zero": beats},
        "A_minus_chance": {"delta": (mean(to_true) - mean(to_chance)) if to_true and to_chance else None,
                           "ci": d_chance,
                           "excludes_zero": (None if not (to_true and to_chance) else
                                             d_chance[0] is not None
                                             and (d_chance[0] > 0 or d_chance[1] < 0))},
        "decoys": decoys,
    }


# ---------------------------------------------------------------- the run
def run_arm(lens, n, rng, label, relay):
    texts, attempts, misses = [], [], 0
    for i in range(n):
        t, a = read_once(lens, rng, relay=relay)
        attempts.append(a)
        if t is None:
            misses += 1
        else:
            texts.append(t)
        print(f"  {label} {i+1}/{n}: {t if t else '(no profile-valid reading in 4 tries)'}",
              file=sys.stderr, flush=True)
    return texts, attempts, misses


def by_position(tokenized, lens):
    """WHERE the agreement sits, per slot and split by word length.

    This is the discriminator that a single pooled agreement number hides. English
    puts its determiners and copulas in the short slots, and a length-3 slot at the
    head of a sentence is answered "the" by almost any reader — so a pooled score
    can be several times the random floor while every content position sits on it.
    Reported for every arm, including the control arms, so the comparison is like
    for like."""
    if len(tokenized) < 2:
        return None
    n = min(len(t) for t in tokenized)
    per = []
    for i in range(n):
        col = [t[i] for t in tokenized]
        pairs = [(col[a], col[b]) for a in range(len(col)) for b in range(a + 1, len(col))]
        per.append(sum(1 for x, y in pairs if x == y) / len(pairs) if pairs else None)
    short = [per[i] for i in range(n) if lens[i] <= 3 and per[i] is not None]
    long = [per[i] for i in range(n) if lens[i] >= 5 and per[i] is not None]
    return {"per_position": [{"len": lens[i], "agreement": per[i]} for i in range(n)],
            "short_words_le3": mean(short) if short else None,
            "content_words_ge5": mean(long) if long else None}


def summarize(name, tokenized, raw_texts, rng, use_embed):
    pos = pairwise(tokenized, positional_agreement)
    jac = pairwise(tokenized, jaccard)
    res = {"n_texts": len(tokenized), "n_pairs": len(pos),
           "positional": {"mean": mean(pos) if pos else None, "ci": boot_ci(pos, rng)},
           "jaccard": {"mean": mean(jac) if jac else None, "ci": boot_ci(jac, rng)}}
    if use_embed and raw_texts:
        vecs = [embed(t) for t in raw_texts]
        cos = pairwise(vecs, cosine)
        res["cosine"] = {"mean": mean(cos) if cos else None, "ci": boot_ci(cos, rng)}
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", default="The night is long and the city keeps its silence",
                    help="the known message to encode")
    ap.add_argument("-n", "--readings", type=int, default=12, help="readings per arm")
    ap.add_argument("--seed", type=int, default=20260830)
    ap.add_argument("--relay", default=os.environ.get("SILENT_RELAY", "mesh-relay"),
                    help="command taking a prompt as argv[1] and printing the reply")
    ap.add_argument("--no-vocab-call", action="store_true",
                    help="skip the vocabulary request; pool the random basis from arm B "
                         "alone (SMALL alphabet — inflates the floor, see vocabulary_pool)")
    ap.add_argument("--no-embed", action="store_true",
                    help="skip the semantic metric (no ollama available)")
    ap.add_argument("--out", default="measure/result.json")
    a = ap.parse_args()

    rng = random.Random(a.seed)
    lens = lengths_of(a.text)
    if not lens:
        sys.exit("the message has no words")
    alt = resample_lengths(lens, rng)

    print(f"message : {a.text}", file=sys.stderr)
    print(f"encoded : {encode(a.text, random.Random(a.seed))}", file=sys.stderr)
    print(f"lengths : {lens}   (arm B uses {alt})", file=sys.stderr)
    print(f"arms    : A treatment, B prior-control, C random basis · n={a.readings}\n",
          file=sys.stderr)

    A, A_att, A_miss = run_arm(lens, a.readings, rng, "A", a.relay)
    B, B_att, B_miss = run_arm(alt, a.readings, rng, "B", a.relay)

    # Arm C's alphabet is message-independent by construction, and never pooled from
    # A: pooling A's own words would let A's convergence raise the floor it is being
    # measured against. The control arm's words are merged in so the basis cannot be
    # missing a length the readings actually used.
    vocab = {} if a.no_vocab_call else vocabulary_pool(rng, a.relay)
    lex_src = "reader-vocabulary+B" if vocab else "B-readings-only(SMALL — floor inflated)"
    lex = merge_lexicons(vocab, pool_lexicon(B)) if vocab else (pool_lexicon(B) or pool_lexicon(A))
    lex_size = sum(len(v) for v in lex.values())
    print(f"random-basis alphabet: {lex_size} words from {lex_src}", file=sys.stderr)
    C = random_basis(lens, lex, rng, a.readings)

    tokA = [words_of(t.lower()) for t in A]
    tokB = [words_of(t.lower()) for t in B]
    C_texts = [" ".join(w for w in c if w) for c in C]

    use_embed = not a.no_embed
    if use_embed:
        try:
            embed("probe")
        except Exception as e:
            print(f"note: no embedding backend ({e}) — semantic metric skipped", file=sys.stderr)
            use_embed = False

    out = {
        "provenance": provenance(sys.argv, a.relay, EMBED_MODEL, use_embed),
        "message": a.text, "lengths": lens, "alt_lengths": alt,
        "readings_requested": a.readings, "seed": a.seed,
        # The WORDS, not only the count. recover_recompute.py used to rebuild this
        # pool from texts C+B, which is a strict subset — measured 163 of 303 words
        # on msg1 and 187 of 337 on msg2 — so a post-hoc floor was drawn from a
        # different alphabet than the run's own and was not comparable to it.
        "random_basis_alphabet": {"source": lex_src, "words": lex_size, "lexicon": lex},
        "compliance": {  # can the reader even hit the length profile? a finding in itself
            "A": {"valid": len(A), "misses": A_miss, "mean_attempts": mean(A_att)},
            "B": {"valid": len(B), "misses": B_miss, "mean_attempts": mean(B_att)},
        },
        "arms": {
            "A_treatment":    summarize("A", tokA, A, rng, use_embed),
            "B_prior_control": summarize("B", tokB, B, rng, use_embed),
            "C_random_basis":  summarize("C", [[w for w in c] for c in C], C_texts, rng, use_embed),
        },
        "where_the_agreement_sits": {
            "A_treatment":     by_position(tokA, lens),
            "B_prior_control": by_position(tokB, alt),
            "C_random_basis":  by_position([[w for w in c] for c in C], lens),
        },
        "texts": {"A": A, "B": B, "C": C_texts},
    }

    # RECOVERY is a different question from CONVERGENCE, and it needs the SAME two
    # floors the convergence arm has. One entry point, shared with the post-hoc
    # recompute, so the two cannot drift again — see recovery_block().
    if use_embed and A:
        out["recovery"] = recovery_block(a.text, A, B, C_texts, lens, lex, rng)

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    def row(name, arm):
        g = lambda k: (arm.get(k) or {}).get("mean")
        fmt = lambda v: "  n/a " if v is None else f"{v:.3f}"
        return (f"  {name:<16} pairs={arm['n_pairs']:>4}  positional={fmt(g('positional'))}"
                f"  jaccard={fmt(g('jaccard'))}  cosine={fmt(g('cosine'))}")

    print("\n== agreement BETWEEN independent readings (higher = more convergent) ==")
    print(row("A treatment", out["arms"]["A_treatment"]))
    print(row("B prior-ctrl", out["arms"]["B_prior_control"]))
    print(row("C random basis", out["arms"]["C_random_basis"]))
    print("\n== where that agreement sits (content words are the ones that would carry a message) ==")
    for nm, key in (("A treatment", "A_treatment"), ("B prior-ctrl", "B_prior_control"),
                    ("C random basis", "C_random_basis")):
        w = out["where_the_agreement_sits"].get(key)
        if not w:
            continue
        f = lambda v: "  n/a " if v is None else f"{v:.3f}"
        print(f"  {nm:<16} short words (<=3 letters)={f(w['short_words_le3'])}"
              f"   content words (>=5)={f(w['content_words_ge5'])}")
    if "recovery" in out:
        r = out["recovery"]
        print("\n== recovery of the INTENDED message ==")
        print("  cosine SIMILARITY — higher = closer. The test is A vs the PRIOR arm;")
        print("  the decoy and random floors are chance, and beating chance is not recovery.")
        def row(label, k, note=""):
            a = r[k]
            v = f"{a['mean']:.3f}  CI {a['ci']}" if a["mean"] is not None else "n/a — no valid readings"
            print(f"  {label} : {v}   n={a['n']}{note}")
        row("A treatment  -> true", "to_true")
        row("B prior ctrl -> true", "to_prior", "   <- the floor that decides")
        row("C random     -> true", "to_chance")
        row("matched decoys      ", "to_decoy")
        dp = r["A_minus_prior"]
        d = f"{dp['delta']:+.4f}  CI {dp['ci']}" if dp["delta"] is not None else "n/a"
        print(f"  A - B_prior = {d}  ->  {r['verdict']}")
    pv = out["provenance"]
    print(f"\nartifact: {a.out}")
    print(f"instrument: {pv['at_start']['git_head'][:12]}"
          f"{'+dirty' if pv['at_start']['instrument_dirty'] else ''}"
          f" sha {pv['at_start']['script_sha256'][:12]}"
          f"{'  INSTRUMENT CHANGED MID-RUN: ' + ','.join(pv['changed_mid_run']) if pv['changed_mid_run'] else ''}"
          f"{'  (tree HEAD moved; instrument bytes did not)' if pv['tree_moved_mid_run'] and not pv['changed_mid_run'] else ''}")


if __name__ == "__main__":
    main()
