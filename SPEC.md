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

Measured, and then a choice. `measure/transport.py` renders six candidate notations
through a file, flowed HTML, `<pre>`, and GitHub's own markdown renderer read *at a
reader* (innerText after layout) rather than at the wire. Full table in
[`measure/result-transport.json`](measure/result-transport.json); the deciding column:

| notation | flowed HTML | GitHub markdown, as read |
|---|---|---|
| `◆◆◆ ◇◇◇◇◇` symbols | intact | intact |
| `"   \t     "` spaces | corrupted **loudly** | corrupted **loudly** |
| `(   ) (     )` brackets | corrupted **SILENTLY** | corrupted **SILENTLY** |
| `··· ·····` dots | intact | intact |
| `___ _____` underscore | intact | corrupted **loudly** |
| `▁▁▁ ▁▁▁▁▁` block | intact | intact |

**The measurement eliminates three of the six; it does not pick among the other three.**
`symbols`, `dots` and `block` are intact in every medium tested, and choosing `▁` over `·`
is preference, not evidence. What the evidence does settle:

- **Brackets fail SILENTLY, and that is the worst way to fail.** A run of spaces collapses
  when a browser lays it out, so `(   )` arrives as `( )` — a *well-formed one-letter
  word*. The reader receives a different message and has no way to know. Nothing else in
  the table does this.
- **An ASCII underscore line is a horizontal rule in markdown**, so the message does not
  arrive at all. That is loud rather than silent — the reader sees a rule and no text —
  but it is still a total loss, and appending a full stop to rescue it is not a protocol.
- **`symbols` survives every medium and was still removed**, for a reason no transport
  test can see: the writer's free choice of glyph is a side channel.

So the field narrows to `dots` and `block` on evidence, and `▁` is chosen from those two
because repeated it joins into a continuous low line — the picture of an elision rather
than of an ellipsis. That last step is taste, and is labelled as taste.

## Decoding (reader)

- Count each run. That is the entire input: a list of word lengths.
- Write a sentence with exactly those word lengths, in that order.
- The reader may be a language model, a person, or anything else that generates text.
- No reading is authoritative, and **no reading is a decoding** — the channel does not
  contain the sentence. `measure/ceiling.py` puts a number on that: a word's length is
  worth 3.30 bits against the word's 11.28, so a reader supplies ~7.99 bits per word,
  roughly 253 equiprobable words per slot.

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
