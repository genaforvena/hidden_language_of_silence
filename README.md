# Silent Language

A deliberately incomplete writing system. A sentence is transmitted as its word lengths
and nothing else. The writer supplies rhythm; the reader supplies everything else, and
`measure/ceiling.py` says how much everything else is: about 8.42 bits per word, roughly
343 equiprobable words per slot. No reading is a decoding, because the sentence is not in
the channel.

The normative document is [`SPEC.md`](SPEC.md). This file is the tour.

## Protocol

- A word becomes a run of `▁` (U+2581), one per letter.
- Words are separated by a single space.
- Nothing else is written.

```
The night is long

The     ▁▁▁      3
night   ▁▁▁▁▁    5
is      ▁▁       2
long    ▁▁▁▁     4
```

On the wire that is one line: `▁▁▁ ▁▁▁▁▁ ▁▁ ▁▁▁▁`

Another, with a longer word so the runs are worth counting:

```
Rain fell across the empty parking structure

Rain        ▁▁▁▁          4
fell        ▁▁▁▁          4
across      ▁▁▁▁▁▁        6
the         ▁▁▁           3
empty       ▁▁▁▁▁         5
parking     ▁▁▁▁▁▁▁       7
structure   ▁▁▁▁▁▁▁▁▁     9
```

There is **one mark**, so the writer makes no choice, and a choice nobody makes cannot
smuggle a message. Earlier versions let the writer pick a symbol per word and that
freedom carried meaning — `U+2601 CLOUD` and `U+2717 BALLOT X` were struck from the set
for exactly that.

The mark is `▁` and not an underscore because that was **measured**, not preferred: a
line of ASCII underscores and spaces is a *horizontal rule* in markdown, so on GitHub the
message does not arrive at all. Runs of literal spaces — the previous protocol, and the
bracket form `(   )` that replaced it — collapse in flowed HTML to `( )`, a well-formed
one-letter word, so the reader gets a different message and cannot tell. The full
six-notation table is in [`SPEC.md`](SPEC.md#why-this-mark) and
[`measure/result-transport.json`](measure/result-transport.json).

The separator has to differ from the mark. Were both the same, `6 + gap + 8` would be
fourteen marks in a row and one fourteen-letter word would be indistinguishable from two
— not a legibility problem, the channel ceasing to be decodable.

Reference implementation: [`silent.py`](silent.py) — `encode()` and `lengths()`, which is
the whole surface.

## Decoding

The reader gets a list of word lengths. That is the whole input. They write a sentence
with exactly those lengths, in that order — a language model, a person, anything that
generates text. Nothing else is supplied and nothing else is checked.

A reading can be encoded again and passed on. Nothing survives the cycle except the
length sequence, which is the point.

```
The night is long   ->   ▁▁▁ ▁▁▁▁▁ ▁▁ ▁▁▁▁   ->   Own rhythm so cold
```

Both sentences encode to that same line. Neither is the decoding of the other, because
there is no decoding: those four runs admit an enormous number of English sentences, and
these are two of them.

## Why LLMs?

A model will always produce a fluent sentence at the requested lengths, so it turns the
gap between "a reading" and "the message" into something measurable instead of arguable:
hand the same skeleton to twenty independent processes and the spread is the evidence.

This section used to also assert **"they never recover intended meaning."** It was the
most interesting sentence in the repository and nobody had ever checked it, so
[`measure/`](measure/) checks it. **The result is a null that is not yet a measured
negative**, and saying so took two wrong floors and an outside review — see below.

## Is any of this measured?

Yes, now. [`measure/`](measure/) encodes a known text, takes N *independent* readings
(separate processes — one sampled list is not N readings) and asks two questions the
project had only ever asserted answers to.

**Do independent readings agree with each other more than chance?** Against a
length-matched, same-alphabet chance arm — message 1 said yes, about four times above
chance, with non-overlapping intervals. Then message 2 was run and the effect
**reversed**. Two messages, opposite verdicts, same instrument.

**Are the readings actually nearer the intended message?** This is the recovery arm,
and the answer turns entirely on what you compare them against.

| message | A treatment | **B prior control** | C random | matched decoys |
|---|---|---|---|---|
| msg 1 "The night is long…" | 0.2402 | **0.2199** | 0.1594 | 0.1531 |
| msg 2 "Rain fell across…" | 0.1122 | **0.1240** | 0.1160 | 0.1934 |

| message | A − B_prior | verdict |
|---|---|---|
| msg 1 | +0.0203, CI [−0.0453, +0.0835] | **no recovery** |
| msg 2 | −0.0118, CI [−0.0516, +0.0270] | **no recovery** |

Cosine similarity, n=20 readings per arm, computed from the stored readings by
[`recover_recompute.py`](measure/recover_recompute.py) with no new model calls.

The arm first shipped with matched decoys as its floor, and that floor is what made
the two messages appear to disagree: msg 1 beat the decoys and msg 2 did not, so a
reader could quote either. But a decoy is random words at the right lengths, and *any*
fluent sentence about a plausible scene beats it. On msg 1 the decoy floor is 0.153 and
the model-free arm C is 0.159 — the same number. The decoy floor was a **chance** floor
wearing a **prior** floor's name.

Arm B is the floor that decides: real readings, same model, same framing, of a length
sequence that is not this message's. Against chance, msg 1 looks like recovery
(+0.0808, interval excluding 0). Against the prior, the effect is gone, and both
messages say the same thing.

So what the runs support is not "the channel works" and not "the channel is empty". It
is that **agreement between readers is not evidence of recovery, and neither is beating
random text** — two readers converging can be two readers sharing a prior, and the only
arm that separates those is a run on a *different* input.

The full method, the failure modes it walked into, and every per-arm figure are in
[`measure/README.md`](measure/README.md). Every artifact carries a provenance block
naming the instrument that produced it, because one of these results was written by a
version of the code that no longer existed in the tree.

An essay about what went wrong on the way to these numbers:
[*Your models agreed with each other. They were agreeing with themselves.*](https://dev.to/ilya_mozerov_867dbdd91feb/your-models-agreed-with-each-other-they-were-agreeing-with-themselves-3jb0)

## The ceiling — measured without asking a model anything

The recovery result above says readers do not recover the message. The obvious next
question is whether they *could*, and it is answered by counting, not by prompting.

A word's shape is its length. On wikitext-103 (6.89M tokens in the 3–12-word window,
761,273 distinct sentences), a word's length is worth **3.30 bits** and a word carries
**11.72**. What survives encoding is **28.1%** of the word; the reader supplies the
other **8.42 bits**, which is **343 equiprobable words per slot**. A ten-word sentence
leaves ~84 bits to invent.

So the null result is not a failure of the readers — **it is the prediction**. Two
readers handed the same shape are choosing inside the same 343-wide slot with the same
prior, which is exactly what the prior control caught them doing.

One number in that measurement is a trap, and it is the quotable one. Counting how many
distinct corpus sentences share a signature says 84% of signatures are unique — which
invites "then the shape nearly identifies the sentence". It does not: the same count run
at 10%, 25%, 50% and 100% of the corpus gives 91.8% → 88.8% → 86.5% → 83.9%, falling
monotonically with no sign of settling, and the average group a sentence lands in grows
1.4 → 4.8. In-corpus uniqueness is a statement about the corpus's size. A 12-word shape
indexes 2⁴¹ possibilities against 10⁵ available sentences, so its uniqueness is
arithmetically forced and measures nothing at all.

Method, every caveat, the per-length table, and the estimator direction the arm got
backwards until a test caught it: [`measure/README.md`](measure/README.md#the-ceiling-how-much-can-the-channel-carry-at-all).
Artifact: [`measure/result-ceiling.json`](measure/result-ceiling.json). No model, no
network — so this arm cannot be wrong about a *reader*. It can still be wrong about the
CORPUS, and on 2026-08-30 it was: the length distribution was accumulated over word TYPES
instead of TOKENS, and the headline shipped 0.12 bits high until an outside review caught
it. That is the same failure this repository already documents twice — a quantity computed
off the wrong population — arriving in the one arm described as unable to be wrong.

## What the project claims, and what it has stopped claiming

Standing:

- Meaning here is projection. The reader is not recovering, they are composing under a
  constraint, and the numbers above say how loose the constraint is.
- No reading is authoritative, and re-encoding a reading loses everything but the shape.
- **The single mark is the admission.** The writer is given nothing to express with —
  earlier versions let them pick a symbol per word, and that freedom quietly carried
  meaning, which is why it was removed rather than celebrated.

Withdrawn, because it was measured and did not survive contact:

- *"Interception by outsiders is effectively impossible."* Backwards — the channel is
  weak, not strong. See [`ENCRYPTION_USECASE.md`](ENCRYPTION_USECASE.md).
- *"Symbol choice randomness is the clearest admission."* There is no symbol choice now.
- The grandiosity about symbol sets and how to render them, which described a protocol
  this repository no longer uses. [`SPEC.md`](SPEC.md#history) keeps the three forms and
  what each cost, instead of the prose.

## Where it could go

- A public gallery of readings of one skeleton, shown side by side.
- Reader → writer → reader cycles: how fast does the shape itself drift?
- `stage_1/` trains a model on lengths alone. The target is not "did it work" but **how
  close to 3.30 bits per word it gets**, against a control given no input at all.

## Interactive Demo

https://genaforvena.github.io/hidden_language_of_silence/

