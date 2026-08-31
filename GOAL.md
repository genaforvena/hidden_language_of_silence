# What this is, in one page

*Read this instead of the rest. `SPEC.md` is the normative document, `README.md`
is the tour, `measure/README.md` is the method. This file is the summary you can
hold in your head.*

## The project

A writing system that transmits **word lengths and nothing else**, and an
instrument that measures what a reader can actually get back from it.

A word becomes a run of `▁`, one mark per letter; words are separated by a space;
nothing else is written. `The night is long` goes out as `▁▁▁ ▁▁▁▁▁ ▁▁ ▁▁▁▁`. What
survives encoding is one sequence of numbers, so every reading — human or model —
comes from that sequence plus the reader's own prior.

Two halves, and they are different kinds of thing:

- **the artefact** — a deliberately incomplete writing system. The writer supplies
  rhythm; the reader supplies everything else.
- **the instrument** — [`measure/`](measure/), which tests the claims the artefact
  makes about itself. The README once asserted that readers "never recover
  intended meaning" and nobody had checked. That is what `measure/` is for.

## The one question

**When several readers of the same silent message agree with each other, what are
they agreeing with?**

The intuitive answer is "the message". The measured answer is that agreement
between readers is not by itself evidence of anything about the channel: two
readers converging can be two readers sharing a prior, and separating those needs
a control arm that reads a *different* input.

## What has been established

**The ceiling — no model asked, so this arm cannot be wrong about a reader.**
On wikitext-103 (6.89M tokens in the 3–12-word window), a word's length is worth
**3.30 bits** where the word itself carries **11.28**. Encoding keeps **29.2%**;
the receiver supplies the other **7.99 bits** — about **253 equiprobable words per
slot**, ~80 bits for a ten-word sentence.

**So the null result below is not a failure of the readers. It is the prediction.**
Two readers handed the same shape are choosing inside the same 253-wide slot with
the same prior, which is exactly what the prior control caught them doing.

| claim | status |
|---|---|
| Readings are nearer the intended message than a **prior-matched** control | **no.** msg 1 `+0.0203 CI [−0.0453,+0.0835]`; msg 2 `−0.0118 CI [−0.0516,+0.0270]` |
| Readers agree with each other more than chance | **unstable** — msg 1 yes (≈4× chance), msg 2 reversed. Two messages, opposite verdicts, one instrument. |
| Readings beat random text | yes, and **it means nothing** — any fluent sentence beats random words at matched lengths |
| "Interception by outsiders is effectively impossible" | **withdrawn.** Backwards: the channel is weak, not strong. |

Cosine similarity, n=20 **independent** readings per arm (separate processes — one
sampled list is not n readings), recomputed offline from stored readings by
[`recover_recompute.py`](measure/recover_recompute.py).

## The durable results are methodological

Three, and each cost a wrong answer first:

1. **The floor decides the verdict, and the obvious floor is the wrong one.** The
   recovery arm first used *matched decoys* — random words at the right lengths.
   On msg 1 that floor reads `0.153` and the model-free arm reads `0.159`: the
   same number. It was a **chance floor wearing a prior floor's name**, and under
   it the two messages appeared to disagree. Against the arm that decides — real
   readings of a *different* length sequence — the effect is gone and both
   messages agree.
2. **In-corpus uniqueness is a statement about the corpus's size.** "84% of
   signatures are unique" invites "then the shape nearly identifies the
   sentence". Run at 10/25/50/100% of the corpus it gives 91.8 → 88.8 → 86.5 →
   83.9%, falling monotonically with no sign of settling. A 12-word shape indexes
   2⁴¹ possibilities against 10⁵ available sentences; its uniqueness is
   arithmetically forced.
3. **A quantity computed off the wrong population.** The ceiling accumulated its
   length distribution over word **types** instead of **tokens** and shipped 0.12
   bits high until an outside review caught it — in the one arm described as
   unable to be wrong.

## Data

Every result file carries a provenance block naming the instrument that produced
it, including the script's own SHA-256, because one result had been written by a
version of the code that no longer existed in the tree. Artefacts:
`measure/result-ceiling*.json`, `measure/result-msg{1,2}-stamped.json`,
`measure/result-constraints-*.json`, `measure/result-transport.json`.

Numbers here can be falsified without spending a token: `recover_recompute.py`
re-derives the recovery table from stored readings with no model calls, and
`ceiling.py` asks no model at all.

## Where it goes next

1. **A third message.** Two gave opposite agreement verdicts; n=2 cannot separate
   message-dependence from noise.
2. **`stage_1/` trains on lengths alone** — and the target is *not* "did it work"
   but **how close to 3.30 bits per word it gets**, against a control given no
   input at all.
3. **Publish the negative.** "Agreement between readers is not evidence of
   recovery" is the sentence that generalises past this toy.

## What is belief and not measurement

Meaning here is projection: the reader is not recovering, they are composing under
a constraint, and the numbers say how loose the constraint is. The single mark is
the admission — the writer is given nothing to express with, because earlier
versions let them pick a symbol per word and that freedom quietly carried meaning.

Those are commitments, not findings. Keeping them in their own section is the
point of having this file: everything above is falsifiable, this paragraph is not.

## Licence

MIT. Demo: https://genaforvena.github.io/hidden_language_of_silence/
