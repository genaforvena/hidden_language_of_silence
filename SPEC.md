# The Silent Language spec

One document, one protocol. If anything else in this repository describes a different
encoding, that other thing is stale and this file wins.

## Encoding (writer)

- A word becomes a run of `▁` (U+2581 LOWER ONE EIGHTH BLOCK), one per letter.
- Words are separated by a single space.
- Nothing else is written.

```
The night is long
▁▁▁ ▁▁▁▁▁ ▁▁ ▁▁▁▁
```

There is **one mark**, so the writer makes no choice, and a choice nobody makes cannot
smuggle a message. That is the entire reason for the mark being fixed — not economy of
appearance. The first version of this protocol let the writer pick a fresh symbol per
word, and that freedom *was* a side channel: `U+2601 CLOUD` and `U+2717 BALLOT X` were
struck from the set for carrying pictures.

The separator has to differ from the mark. Were both the same, `6 + gap + 8` would be
fourteen marks in a row and one fourteen-letter word would be indistinguishable from
two. That is not a legibility problem — the channel stops being decodable.

## Why this mark

Measured, not preferred. `measure/transport.py` renders six candidate notations through
a file, flowed HTML, `<pre>`, and GitHub's own markdown renderer read *at a reader*
rather than at the wire. Full table in
[`measure/result-transport.json`](measure/result-transport.json); the two rows that
decided it:

| notation | flowed HTML | GitHub markdown, as read |
|---|---|---|
| `(   ) (     )` brackets | **corrupted silently** | **corrupted silently** |
| `___ _____` underscore | intact | **corrupted silently** |
| `▁▁▁ ▁▁▁▁▁` block | intact | intact |

A run of spaces collapses to one space when a browser lays it out, so `(   )` arrives as
`( )` — a *well-formed one-letter word*. The reader receives a different message and
cannot tell. An ASCII underscore is worse in markdown: a line made only of underscores
and spaces is a horizontal rule, so the message does not arrive at all. Appending a full
stop rescues it, which is not a protocol.

`▁` draws the underscore's picture — repeated, the glyphs join into a continuous low
line — while being ordinary text to every parser and non-collapsing in every renderer.

## Decoding (reader)

- Count each run. That is the entire input: a list of word lengths.
- Write a sentence with exactly those word lengths, in that order.
- The reader may be a language model, a person, or anything else that generates text.
- No reading is authoritative, and **no reading is a decoding** — the channel does not
  contain the sentence. `measure/ceiling.py` puts a number on that: a word's length is
  worth 3.42 bits against the word's 11.72, so a reader supplies ~8.42 bits per word,
  roughly 343 equiprobable words per slot.

## Re-encoding

A reading can be encoded again and handed on. Nothing survives the cycle except the
length sequence, which is the point.

## History

Four notations were tried. Each removed something and paid for it.

1. **A freely chosen symbol per word.** The free choice was a side channel.
2. **Literal spaces, tab-separated.** Removed the choice and spent all visibility: the
   message could not be shown or moved, and every worked example needed a dot rendering
   beside it. The dots were doing the work while being labelled debug.
3. **Brackets around a run of spaces** — `(   )`. Nothing stands for a letter; only the
   boundary of the gap is drawn, the way an editor marks an elision. The best idea of
   the four and the one that fails worst in practice, silently.
4. **A run of `▁`, space-separated.** One fixed mark, no writer's choice, survives every
   medium measured. Current.
