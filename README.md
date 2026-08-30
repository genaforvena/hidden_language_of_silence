# Silent Language — Project README

## Overview
Silent Language is a deliberately incomplete writing system. It encodes sentences as sequences of arbitrary non-linguistic symbols, each symbol cluster’s length corresponding to a word length. The system rejects stable meaning. Writers provide rhythm; readers hallucinate content. No reading is definitive. Every interpretation is ephemeral.

## Protocol
### Encoding (Writer)
- Each word becomes a run of **spaces**, one space per letter.
- Words are separated by a **tab**.
- Nothing else is written. The encoded message is entirely whitespace.

The channel is the sequence of word lengths and nothing else — not because the symbols
were chosen to carry no meaning, but because **there are no symbols**. A reader receives
a shape of silence.

The separator has to be something other than a space. If the gaps between words were
spaces too, `6 + gap + 8` would be fifteen spaces in a row, and one fifteen-letter word
would be indistinguishable from two words. That is not a legibility problem, it is the
channel ceasing to be decodable.

Example. The dot column is what is actually transmitted, with `·` standing in for each
space — **the dots are not part of the encoding**; a real run of spaces cannot be shown on
a page. The number is that run's length, which is the entire channel.

```
Silent language fails beautifully

Silent        ······         6
language      ········       8
fails         ·····          5
beautifully   ···········   11
```

Another:

```
The night is long

The     ···      3
night   ·····    5
is      ··       2
long    ····     4
```

Reference implementation: [`silent.py`](silent.py). `encode()` returns the real
whitespace; `visible()` is a debug rendering only. A visible stand-in for a space is a
symbol again, and symbols are what this encoding exists to remove.

**A note on displaying it.** HTML and Markdown collapse consecutive spaces, so a raw
encoded message pasted into a web page renders as a single space and looks like nothing
at all. Anything that shows the channel must preserve whitespace — a fenced code block, a
`<textarea>`, or `white-space: pre`. This is a property of the medium, not a defect in the
encoding, but it will bite anyone who forgets it.

### Decoding (Reader)
- The reader uses only length to guess words.
- No semantic hint comes from symbols.
- LLMs or humans fill blanks with context-dependent hallucinations.
- Re-encoding produces new symbol sets each cycle.

## Usage
- Encode text with the writer.
- Submit encoded strings to the reader.
- Capture interpretations.
- Compare multiple readings for diversity.

## Example
Original:
```
The night is long

The    ···  3
night  ·····  5
is     ··  2
long   ····  4
```
△︎△︎△︎ ◇︎◇︎◇︎◇︎◇︎ ◎︎◎︎ ◇︎◇︎◇︎◇︎
 3    5   2   4
```
Reader interpretation:
```
Own rhythm so cold
```

## Why LLMs?
- LLMs act as reflection engines.
- They generate from structure and bias.
- They demonstrate linguistic drift.
- Their outputs embody unpredictable projections.

This section used to also assert **"they never recover intended meaning."** It was the
most interesting sentence in the repository and nobody had ever checked it, so
[`measure/`](measure/) checks it. **The sentence holds**, and it took two wrong floors
to establish that — see below.

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
761,273 distinct sentences), a word's length is worth **3.42 bits** and a word carries
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
network — this arm cannot be wrong about a reader, because it never asks one.

## Philosophical Grounding
- No text carries meaning inherently.
- Meaning is projection, hallucination, negotiation.
- The protocol is a stage for constraint and chaos.
- Every reading is proof that language fails.
- Symbol choice randomness is the clearest admission of this.

## Potential Directions
- Interactive playgrounds for encoded structures.
- Public galleries showcasing diverse hallucinations.
- Recursion experiments (reader → writer → reader cycles).
- Visual installations where text structures remain static but readings rotate.
- Evidence of my insanity.

## Rendering

Every symbol in this project must be pinned to **text presentation** with `U+FE0E`.

Several of the glyphs used here — `U+25FC BLACK MEDIUM SQUARE` above all — have *default
emoji presentation* in Unicode. A font is then free to draw them as full-colour, double-width
emoji, and at double width the single space between clusters is visually swallowed. Word
boundaries stop being visible, and word boundaries are the entire channel: a reader who cannot
see where one cluster ends has not been given a shorter message, they have been given a
different one.

Two glyphs were removed from the symbol set outright rather than re-rendered: `U+2601 CLOUD`
and `U+2717 BALLOT X`. The protocol says symbol choice carries no message. A picture of a cloud
and a rejection mark both carry one.

## Interactive Demo

https://genaforvena.github.io/hidden_language_of_silence/

