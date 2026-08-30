#!/usr/bin/env python3
"""The recovery arm's floor, tested against the failure it actually had.

The bug was not a crash. The arm compared arm-A readings to the true message against
LENGTH-MATCHED DECOYS and called beating them recovery. Decoys are random words: any
fluent English sentence about a plausible scene beats them, having recovered nothing.
On the live artifacts the decoy floor sat at 0.153 while arm B — real readings, same
model, same framing, a DIFFERENT length sequence — sat at 0.220, and the gap between
those two floors is the entire apparent result.

So the arm under test here is: does the verdict move when A is lifted off the decoys
but NOT off the prior? Under the old floor that case reads "recovery". It must not.

No embedding backend is needed: recovery_block takes its embedder as an argument, so
the geometry is constructed rather than sampled. That also means this test can assert
things a live run never could, like two arms being exactly equal.
"""
import math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import silent_channel as sc

FAILS = []


def check(name, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}{'  — ' + detail if detail else ''}")
    if not ok:
        FAILS.append(name)


# ---------------------------------------------------------------- fake geometry
VOCAB = [f"w{i}" for i in range(24)]


def fake_embed(text):
    """Bag-of-words over a fixed vocabulary: cosine is then a real angle between
    texts, so 'closer to the message' means sharing its words."""
    v = [0.0] * len(VOCAB)
    for w in text.lower().split():
        if w in VOCAB:
            v[VOCAB.index(w)] += 1.0
    if not any(v):          # unknown words still need a direction, or cosine is None
        v[hash(text) % len(VOCAB)] = 0.5
    return v


TRUE = " ".join(VOCAB[:8])


# A single-bucket lexicon cannot tell a length-matched decoy from an unmatched one:
# every draw is the same length whatever the code does. The buckets differ here so
# the matching is actually under test.
LENS = [2, 3, 5, 3, 7, 4]
LEX = {n: [chr(ord("a") + n) * n + str(i) for i in range(12)] for n in set(LENS)}


def block(A, B, C, seed=1):
    return sc.recovery_block(TRUE, A, B, C, LENS, LEX, random.Random(seed),
                             embed_fn=fake_embed)


def main():
    print("== the two arms the verdict must separate ==")

    # A and B share the message's words EQUALLY: fluent, on-topic, no channel.
    # Both sit far above the decoy floor, which is the case that used to read
    # "recovery" and must now read no-recovery.
    # Drawn from ONE pool by two different draws, so the arms have real variance and
    # the bootstrap has something to do — identical texts would give a degenerate
    # zero-width interval that includes 0 for free, an arm that cannot fail.
    pool = [" ".join(VOCAB[i:i + 4]) for i in range(6)]
    dr = random.Random(11)
    same = [dr.choice(pool) for _ in range(12)]
    other = [dr.choice(pool) for _ in range(12)]
    r = block(same, other, ["q1 q2 q3"] * 12)
    check("two draws from one pool read NO recovery",
          "NO recovery" in r["verdict"], r["verdict"])
    check("...even though A beats the decoy floor",
          r["to_true"]["mean"] > r["to_decoy"]["mean"],
          f"to_true {r['to_true']['mean']:.3f} > decoy {r['to_decoy']['mean']:.3f}")
    check("A - B_prior interval includes 0, and is not zero-width",
          (not r["A_minus_prior"]["excludes_zero"]
           and r["A_minus_prior"]["ci"][0] < r["A_minus_prior"]["ci"][1]),
          str(r["A_minus_prior"]["ci"]))

    # Now give A the message's words and B unrelated ones: a real channel.
    A = [" ".join(VOCAB[:8]) for _ in range(12)]
    B = [" ".join(VOCAB[12:20]) for _ in range(12)]
    r2 = block(A, B, ["q1 q2 q3"] * 12)
    check("A genuinely nearer than B reads RECOVERY",
          r2["A_minus_prior"]["excludes_zero"] and "NO recovery" not in r2["verdict"],
          r2["verdict"])
    check("the two cases give opposite verdicts",
          r["A_minus_prior"]["excludes_zero"] != r2["A_minus_prior"]["excludes_zero"])

    print("\n== every arm carries an interval (the drift the recompute had) ==")
    for k in ("to_true", "to_prior", "to_chance", "to_decoy"):
        v = r2[k]
        check(f"{k} has mean, ci and n",
              v["mean"] is not None and v["ci"][0] is not None and v["n"] == 12)
    for k in ("A_minus_prior", "A_minus_chance"):
        check(f"{k} has a difference interval",
              r2[k]["ci"][0] is not None and r2[k]["delta"] is not None)

    print("\n== the prior floor is a DIFFERENT number from the chance floors ==")
    # This is the live geometry: on result-msg1-stamped.json the decoy floor is 0.153
    # and the prior floor 0.220. An arm sitting between them reads "recovery" under
    # the old floor and "no recovery" under this one — which is the whole bug.
    check("a fluent on-topic prior sits ABOVE the decoy floor",
          r["to_prior"]["mean"] > r["to_decoy"]["mean"],
          f"prior {r['to_prior']['mean']:.3f} vs decoy {r['to_decoy']['mean']:.3f}")
    check("and arm A sits above the decoy floor too, yet loses",
          r["to_true"]["mean"] > r["to_decoy"]["mean"] and "NO recovery" in r["verdict"])
    check("verdict is not a function of to_decoy",
          "NO recovery" in block(same, list(same), ["q1 q2 q3"] * 12)["verdict"])

    print("\n== a blind arm must not wear a verdict (found by the first live drive) ==")
    # At n=6 the reader missed the length profile on all six CONTROL readings, so the
    # prior arm was n=0 — and the block still said "NO recovery above the prior
    # (A - B_prior includes 0)". The failure direction is the bad one: no-recovery is
    # also the TRUE answer, so a blind run agrees with the real ones and cannot be
    # told apart from them.
    blind = block(A, [], ["q1 q2 q3"] * 12)
    check("empty prior arm -> UNKNOWN, not a recovery verdict",
          blind["verdict"].startswith("UNKNOWN"), blind["verdict"])
    check("...and it names which arm is missing", "B_prior" in blind["verdict"])
    check("excludes_zero is None, not False (False is a measured negative)",
          blind["A_minus_prior"]["excludes_zero"] is None,
          repr(blind["A_minus_prior"]["excludes_zero"]))
    check("the blind verdict differs from the real no-recovery verdict",
          blind["verdict"] != r["verdict"])
    check("the surviving arms still report their numbers",
          blind["to_true"]["mean"] is not None and blind["to_prior"]["n"] == 0)
    blindA = block([], list(same), ["q1 q2 q3"] * 12)
    check("empty TREATMENT arm is UNKNOWN too",
          blindA["verdict"].startswith("UNKNOWN") and "A_treatment" in blindA["verdict"],
          blindA["verdict"])

    print("\n== the decoys carry the message's length profile ==")
    # A decoy floor that is not length-matched is not a matched floor: a reading
    # could then be nearer the truth than a decoy for its shape alone.
    prof = [[len(w.rstrip("0123456789")) for w in d.split()] for d in r2["decoys"]]
    check("every decoy has the message's word count",
          all(len(x) == len(LENS) for x in prof), str(prof[:1]))
    check("every decoy word matches its slot's length",
          all(x == LENS for x in prof), f"want {LENS}, got {prof[0] if prof else None}")

    print("\n== boot_diff_ci ==")
    rng = random.Random(3)
    lo, hi = sc.boot_diff_ci([0.5] * 20, [0.5] * 20, rng)
    check("identical arms -> interval containing 0", lo <= 0 <= hi, f"[{lo}, {hi}]")
    lo, hi = sc.boot_diff_ci([0.9] * 20, [0.1] * 20, rng)
    check("separated arms -> interval excluding 0", lo > 0, f"[{lo}, {hi}]")
    check("an empty arm returns no interval", sc.boot_diff_ci([], [1.0], rng) == (None, None))
    check("an empty FIRST arm returns no interval too",
          sc.boot_diff_ci([1.0], [], rng) == (None, None))
    # BOTH arms must be resampled. If only xs is, then a constant xs against a
    # spread-out ys gives a zero-width interval — the second arm's uncertainty
    # vanishes and the difference reads as exact.
    lo, hi = sc.boot_diff_ci([0.5] * 40, [0.1, 0.9] * 20, rng)
    check("the SECOND arm's variance reaches the interval", hi - lo > 0.05,
          f"width {hi - lo:.4f} — a constant arm against a spread one must still be wide")

    print(f"\n{len(FAILS)} failure(s)" + (": " + ", ".join(FAILS) if FAILS else ""))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
