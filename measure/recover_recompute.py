#!/usr/bin/env python3
"""Compute the RECOVERY arm from an existing artifact, with no new model calls.

Convergence is model-free (positional agreement over stored words) and always lands.
Recovery needs an embedding backend, and on 2026-08-30 both re-runs hit an ollama
mid-upgrade — every /api/embeddings returned HTTP 500 because the llama-server
binary had been removed before the replacement tarball arrived. The harness did the
right thing: it said so and wrote no `recovery` block, rather than a plausible
number.

That does not cost the 80 model calls again. silent_channel.py stores every reading
in `texts.A`, and the decoys are reconstructed from the same seed and the same
lexicon the run recorded — so recovery is a pure recompute over the artifact once a
backend is available.

  python3 measure/recover_recompute.py measure/result-msg1-stamped.json

It writes the block back into the artifact under `recovery`, tagged with its own
provenance so the file still says which instrument produced which number: the
recovery figures come from THIS script at THIS commit, not from the run that
produced the convergence figures beside them.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import silent_channel as sc


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    d = json.load(open(path))

    if "recovery" in d and "--force" not in sys.argv:
        sys.exit(f"{path} already carries a recovery block; pass --force to replace it")

    A = d["texts"]["A"]
    if not A:
        sys.exit("no arm-A readings in this artifact")

    try:
        sc.embed("probe")
    except Exception as e:
        sys.exit(f"no embedding backend ({e}) — recovery still cannot be computed")

    # The decoys must carry the SAME length profile as the message, or a reading
    # being closer to the truth could be explained by length alone. Rebuilt from the
    # artifact's own lexicon (arm C's texts are drawn from it) at the run's seed.
    import random
    rng = random.Random(d["seed"])
    lens = d["lengths"]
    lex = sc.pool_lexicon(d["texts"]["C"] + d["texts"]["B"])
    decoys = [" ".join(rng.choice(lex[l]) if lex.get(l) else "x" * l for l in lens)
              for _ in range(8)]

    v_true = sc.embed(d["message"])
    v_dec = [sc.embed(x) for x in decoys]
    to_true, to_decoy = [], []
    for t in A:
        v = sc.embed(t)
        c = sc.cosine(v, v_true)
        if c is not None:
            to_true.append(c)
        ds = [x for x in (sc.cosine(v, w) for w in v_dec) if x is not None]
        if ds:
            to_decoy.append(sum(ds) / len(ds))

    from statistics import mean
    d["recovery"] = {
        "metric": "cosine_similarity",
        "direction": "higher = closer to the target",
        "reading": ("to_decoy >= to_true means the readings are no nearer the intended "
                    "message than a length-matched decoy: no recovery"),
        "computed_by": "recover_recompute.py (post-hoc; the run itself had no embedding backend)",
        "computed_provenance": sc.stamp(),
        "n_readings": len(A),
        "to_true":  {"mean": mean(to_true) if to_true else None},
        "to_decoy": {"mean": mean(to_decoy) if to_decoy else None},
        "decoys": decoys,
    }
    with open(path, "w") as f:
        json.dump(d, f, indent=2)
    r = d["recovery"]
    print(f"{path}: n={len(A)}  to_true {r['to_true']['mean']:.4f}  "
          f"to_decoy {r['to_decoy']['mean']:.4f}  "
          f"({'NO recovery' if r['to_decoy']['mean'] >= r['to_true']['mean'] else 'to_true is higher'})")


if __name__ == "__main__":
    main()
