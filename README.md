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
[`measure/`](measure/) checks it. The short answer is that the sentence is not wrong,
but it is not what the first result looks like either — see below.

## Is any of this measured?

Yes, now. [`measure/`](measure/) encodes a known text, takes N *independent* readings
(separate processes — one sampled list is not N readings) and asks two questions the
project had only ever asserted answers to.

**Do independent readings agree with each other more than chance?** Against a
length-matched, same-alphabet chance arm — message 1 said yes, about four times above
chance, with non-overlapping intervals. Then message 2 was run and the effect
**reversed**. Two messages, opposite verdicts, same instrument.

**Are the readings actually nearer the intended message than a length-matched decoy?**
This is the recovery arm, and it agrees with the reversal:

| message | to true text | to decoy | verdict |
|---|---|---|---|
| msg 1 | 0.2402 | 0.1531 | nearer the true text |
| msg 2 | 0.1122 | 0.1934 | **no recovery** |

Cosine similarity, n=20 readings each, computed from the stored readings by
[`recover_recompute.py`](measure/recover_recompute.py) with no new model calls.

What the pair of runs supports is not "the channel works" and not "the channel is
empty". It is that **agreement between readers is not evidence of recovery** — two
readers converging can be two readers sharing a prior, and the arm that separates
those is a run on a *different* input. That arm is arm B, and it is the one that
decides.

The full method, the failure modes it walked into, and every per-arm figure are in
[`measure/README.md`](measure/README.md). Every artifact carries a provenance block
naming the instrument that produced it, because one of these results was written by a
version of the code that no longer existed in the tree.

An essay about what went wrong on the way to these numbers:
[*Your models agreed with each other. They were agreeing with themselves.*](https://dev.to/ilya_mozerov_867dbdd91feb/your-models-agreed-with-each-other-they-were-agreeing-with-themselves-3jb0)

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

