#!/usr/bin/env python3
"""Compute the RECOVERY arm from an existing artifact, with no new model calls.

Convergence is model-free and always lands. Recovery needs an embedding backend, and
on 2026-08-30 both re-runs hit an ollama mid-upgrade — every /api/embeddings returned
HTTP 500 because the llama-server binary had been removed before the replacement
tarball arrived. The harness did the right thing: it said so and wrote no `recovery`
block, rather than a plausible number.

That does not cost the 80 model calls again. silent_channel.py stores every reading,
so recovery is a pure recompute over the artifact once a backend is available.

  python3 measure/recover_recompute.py measure/result-msg1-stamped.json

TWO THINGS THIS SCRIPT USED TO GET WRONG, both found by running it:

**It was a second copy of the scoring code, and it had already drifted** — it shipped
bare means where the inline arm shipped means WITH intervals, so the two artifacts in
this directory carry the same field name under two different standards of evidence.
The scoring now lives in exactly one place, `silent_channel.recovery_block()`, which
both call. That is also where the floor was fixed: the verdict is A minus the PRIOR
arm, not A minus matched decoys.

**It rebuilt the decoy alphabet from texts C+B**, because older artifacts stored only
the SIZE of the run's basis alphabet and not the words. That proxy is a strict
subset — measured 163 of 303 words on msg1 and 187 of 337 on msg2 — so a post-hoc
floor was drawn from a different alphabet than the run's own. Runs now store the
lexicon itself and this script prefers it; on an older artifact it falls back to the
proxy and SAYS SO in the block, because a floor drawn from half the alphabet is a
different measurement wearing the same field name.

It writes the block back tagged with its own provenance, so the file still says which
instrument produced which number: the recovery figures come from THIS script at THIS
commit, not from the run that produced the convergence figures beside them.
"""
import json, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import silent_channel as sc


def basis(d):
    """The run's own alphabet if it stored one, else the C+B proxy — named either way."""
    stored = (d.get("random_basis_alphabet") or {}).get("lexicon")
    if stored:
        return {int(k): v for k, v in stored.items()}, "run's own stored basis alphabet"
    lex = sc.pool_lexicon(d["texts"]["C"] + d["texts"]["B"])
    n = sum(len(v) for v in lex.values())
    declared = (d.get("random_basis_alphabet") or {}).get("words")
    return lex, (f"PROXY rebuilt from texts C+B: {n} words"
                 + (f" of the run's {declared}" if declared else "")
                 + " — the run did not store its lexicon, so this floor is not"
                   " drawn from the alphabet the run used")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    d = json.load(open(path))

    if d.get("recovery") and "--force" not in sys.argv:
        sys.exit(f"{path} already carries a recovery block; pass --force to replace it")

    A = d["texts"]["A"]
    if not A:
        sys.exit("no arm-A readings in this artifact")

    try:
        sc.embed("probe")
    except Exception as e:
        sys.exit(f"no embedding backend ({e}) — recovery still cannot be computed")

    lex, lex_note = basis(d)
    rng = random.Random(d["seed"])
    r = sc.recovery_block(d["message"], A, d["texts"]["B"], d["texts"]["C"],
                          d["lengths"], lex, rng)
    r["computed_by"] = ("recover_recompute.py (post-hoc; the run itself had no "
                        "embedding backend)")
    r["computed_provenance"] = sc.stamp()
    r["decoy_alphabet"] = lex_note
    d["recovery"] = r

    with open(path, "w") as f:
        json.dump(d, f, indent=2)

    dp = r["A_minus_prior"]
    print(f"{path}\n  basis: {lex_note}")
    print(f"  A treatment  -> true : {r['to_true']['mean']:.4f}  n={r['to_true']['n']}")
    print(f"  B prior ctrl -> true : {r['to_prior']['mean']:.4f}  n={r['to_prior']['n']}")
    print(f"  C random     -> true : {r['to_chance']['mean']:.4f}  n={r['to_chance']['n']}")
    print(f"  matched decoys       : {r['to_decoy']['mean']:.4f}")
    print(f"  A - B_prior = {dp['delta']:+.4f}  CI {dp['ci']}")
    print(f"  VERDICT: {r['verdict']}")


if __name__ == "__main__":
    main()
