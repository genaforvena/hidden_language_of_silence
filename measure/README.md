# Does the silent channel carry anything?

The project README asserts that LLM readers "never recover intended meaning."
It is the most interesting claim in this repository and it had never been
measured. This directory measures it.

## What the channel actually carries

Encoding maps each word to a cluster of a freely chosen symbol, repeated
word-length times, and the spec is explicit that symbol choice carries no
message. So the entire channel is the **length sequence** `L = [l1..ln]`.
Nothing else survives encoding. Whatever a reader recovers must come from `L`
plus the reader's own prior — and separating those two is the whole problem.

## The design

Encode a known text, take **N independent readings** (separate processes, no
shared context — a single sampled list is not N readings), and measure how much
the readings agree **with each other**, against an explicit random basis at
**the same lengths and the same alphabet**.

| arm | what it is | what it isolates |
|---|---|---|
| **A** treatment | N readings of the true message's `L` | channel + prior |
| **B** prior control | N readings of a *different* `L'` — same word count, lengths resampled from the same distribution | the prior and the task framing alone, with no particular message behind it |
| **C** random basis | N texts assembled with **no model**: a random word of the right length at each position | the chance floor |

Three agreement metrics, all pairwise within an arm: **positional** (do two
readings pick the same word at the same slot — well defined because every text
in an arm shares a length profile), **Jaccard** over word bags, and **cosine**
over sentence embeddings.

**Recovery is asked separately from convergence.** They are different claims:
readings can agree with each other while all being wrong. So each arm-A reading is
compared to the *true* original — and the comparison that decides is against **arm
B**, which read a different length sequence and never saw this message. Matched-length
decoys and arm C are also scored, as chance floors for context. They are not the test;
see "The recovery arm had the wrong floor" below, which is the main finding of this
directory.

## Two things that will quietly ruin this measurement

**A basis pooled from too few texts is not a floor.** The first version drew arm
C's alphabet from arm B's readings alone. With 7 valid control readings the
vocabulary is so small that the "random" texts are near-duplicates of each
other, and the floor rises to meet the thing it is supposed to sit under —
measured, that inflated the semantic floor to **cosine 0.391, above the model
readings at 0.232**. The alphabet is now requested independently of any message
and merged with the control arm's words; the run prints which source it used and
says so in the artifact when it has to fall back.

**Agreement above chance requires the chance arm to share the lengths AND the
alphabet.** Drop either and the number measures the model's prior instead of the
channel. That is why arm C is length-matched and drawn from the reader's own
vocabulary rather than from a dictionary the model would never use.

Pairwise similarities share texts, so they are not independent; the bootstrap
interval is descriptive, and the argument is carried by arm-against-arm on the
same construction, never by one arm's interval alone.

## A third thing, and it already bit this measurement

**A result file that cannot name the instrument that wrote it is not evidence.**

`result-msg2.json` — the replication that *reverses* the headline of run 1 — was
written at 03:28:14Z by a process launched before the 03:24:31Z commit that added
the per-position breakdown. Python reads its source once, at start: that run
executed the old code to completion and its output came from an instrument that
no longer exists in the tree. Nothing in the file said so. The only trace was a
**missing key**, which is the weakest possible signal and reads exactly like a run
that had nothing to report.

Every artifact now carries a `provenance` block, and the stamp is taken **twice**:

- `at_start` — taken at import, before anything runs. This is what actually
  produced the numbers. A stamp taken only at write time would have recorded the
  commit that was *not* running.
- `at_write` — the tree as it stands when the file lands.
- `changed_mid_run` — names the fields that moved between them, so a mid-run edit
  is *asserted* rather than inferred from an absence.

Each field fails to a string beginning `unknown:` naming which probe failed; a
provenance field that quietly reports a plausible default is worse than none.

### What the field must NOT key on, learned from its own first run

`changed_mid_run` keys on the **instrument's own bytes** (`script_sha256`,
`instrument_dirty`) and never on `git_head`. HEAD is a property of the *tree*: any
commit anywhere in the repo moves it, so on a run of any length it fires almost
always, the field goes permanently true, and a real instrument change then rides in
under exactly that suppression.

This was measured, not reasoned about, and the artifacts in this directory are the
evidence. Both re-runs were launched at `21f344b`; committing the *test file* as
`79594e1` mid-run moved HEAD while
`git rev-parse 21f344b:measure/silent_channel.py` and `79594e1:…` are the same blob
`a1c4c8a8`. `result-msg1-stamped.json` therefore carries
`changed_mid_run: ["git_head"]` and the sentence "the instrument changed under this
run" — **which is false, and it is left in place on purpose.** Its own
`at_start.script_sha256` is `16f716c8…`, which names the pre-fix instrument, so a
reader can date the verdict and disregard it. That is the feature working on itself:
a wrong derived field stays interpretable because the raw stamp under it is intact,
which is why both halves are kept rather than only the verdict.

The arm that would have caught this did not exist, because the only mutation ever
driven was the one that edits the instrument itself — the test could confirm the
alarm but never bound it. `test_provenance.py` now drives both directions.

## Recovery, measured at last — and the answer is no

Convergence is model-free and always lands. Recovery needs an embedding backend, and
both re-runs hit an ollama mid-upgrade: every `/api/embeddings` returned HTTP 500
because the `llama-server` binary had been removed before its replacement arrived. The
artifacts carried `cosine: null` and no `recovery` block — the harness said so instead
of writing a plausible number. That is the correct behaviour and it is why the numbers
below exist at all: `recover_recompute.py` computes the block from the stored readings
once a backend returns, with no new model calls, tagged with its own provenance so the
file still says which instrument produced which number.

The backend came back on 2026-08-30 and both artifacts were recomputed. **The README's
central claim survives.** Readings of the true length sequence are no nearer the
intended message than readings of a *different* length sequence by the same model.

| | msg1 "The night is long…" | msg2 "Rain fell across…" |
|---|---|---|
| A treatment → true | 0.2402 | 0.1122 |
| **B prior control → true** | **0.2199** | **0.1240** |
| C random basis → true | 0.1594 | 0.1160 |
| matched decoys | 0.1531 | 0.1934 |
| **A − B_prior** | **+0.0203, CI [−0.0453, +0.0835]** | **−0.0118, CI [−0.0516, +0.0270]** |

Both intervals contain 0. n=20 readings per arm, cosine over `all-minilm`.

## The recovery arm had the wrong floor, and the wrong floor manufactured a result

This is the finding, and it is the same mistake this directory already documents for
the *convergence* arm, made one ring out.

The arm originally scored arm-A readings against **length-matched decoys** and called
beating them recovery. A decoy is random words at the right lengths. Any fluent English
sentence about a plausible scene beats it — having recovered nothing. Measured: on msg1
the decoy floor is **0.153** and the model-free arm C is **0.159**, the same number. The
decoy floor was a *chance* floor wearing a *prior* floor's name.

Arm B is the floor that decides: real readings, same model, same framing, of a length
sequence that is not this message's. It sits at **0.220** — two thirds of the way from
the chance floor to the treatment arm. Against chance, msg1 reads as recovery
(A − C = +0.0808, CI [+0.0287, +0.1321], excludes 0). Against the prior, the whole
effect is gone.

**The old floor also made the two messages appear to disagree**, which is worse than a
wrong number because it invites picking one. Under the decoy floor msg1 read "recovery"
(0.240 > 0.153) and msg2 read "no recovery" (0.112 < 0.193), and a reader would quote
whichever suited. Under the prior floor both say the same thing.

Two things were checked before blaming the floor, and one of them refuted the first
guess:

- **The decoy draw is not the free parameter.** `to_decoy` was recomputed over 24
  independent decoy draws, and again over draws from half the pool: sd 0.012–0.026, and
  the verdict was 24/24 stable in *both* directions. The floor is stable; it is
  measuring the wrong thing.
- **The post-hoc pool was not the run's own.** `recover_recompute.py` rebuilt the decoy
  alphabet from texts C+B, because artifacts stored only the **size** of the run's basis
  alphabet. That proxy is a strict subset — 163 of 303 words on msg1, 187 of 337 on
  msg2. It did not change the verdict here (previous point), but a floor drawn from half
  the alphabet is a different measurement wearing the same field name. Runs now store
  the lexicon itself; on an older artifact the script falls back to the proxy and
  **names it in the block**.

### Two copies of the scoring code, already drifted

The fix is also a de-duplication, and the duplication had already cost something. The
inline arm and the post-hoc recompute were separate implementations of the same
scoring, and the recompute shipped **bare means with no intervals** where the inline
arm shipped means with intervals — so two files in this directory carried the same
field name under two different standards of evidence, and the weaker one carried the
headline. Scoring now lives in exactly one place, `silent_channel.recovery_block()`,
which both call.

### A blind arm was wearing a verdict, and the failure direction was the bad one

Found by the first live drive of the fixed code, not by the unit tests — every fixture
had readings in every arm. At `-n 6` the reader missed the length profile on **all six**
control readings (`compliance.B.valid: 0`), so the prior arm was `n=0`. The block still
printed **"NO recovery above the prior (A − B_prior includes 0)"**: a claim about an
interval that does not exist.

That is the worst possible direction for it to fail. No-recovery is also the *true*
answer, so a completely blind run agrees with the real ones and cannot be told apart
from them — a run that measured nothing would have corroborated the finding above.
An empty treatment or prior arm now renders `UNKNOWN` naming which arm is missing, and
`excludes_zero` is `None` rather than `False`, because `False` is a measured negative.
The other arms still report their own numbers; only the verdict abstains.

`test_recovery.py` covers it with 14 mutants driven red against a green control,
including the original bug (verdict keyed on the decoy floor), the recompute's missing
intervals, a one-sample difference interval, and each half of the blindness guard. Its fixture had to be fixed twice
before it could discriminate: a single-bucket lexicon cannot tell a length-matched decoy
from an unmatched one, and two identical arms give a zero-width interval that contains 0
for free — an arm that cannot fail.

## The recovery numbers are similarities, not distances

`recovery.to_true`, `to_prior`, `to_chance` and `to_decoy` are **cosine similarities:
higher means closer.** "The readings sit 0.210 from the true original" inverts the
direction and is the sentence a reader will quote, so the artifact carries `metric`,
`direction` and `reading` fields spelling it out. The no-recovery result is
`A_minus_prior.ci` containing 0 — not `to_decoy >= to_true`, which was the old and
wrong test.

## Running it

```bash
python3 measure/silent_channel.py --text "your known message" -n 20
```

Needs a reader command taking a prompt as `argv[1]` and printing the reply
(`--relay`, default `mesh-relay`), and any embedding endpoint for the semantic
metric (`--no-embed` to skip). Every reading, arm and pair lands in the JSON
artifact so the numbers can be recomputed without re-running the models.
