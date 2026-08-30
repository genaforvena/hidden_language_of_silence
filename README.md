# Silent Language — Project README

## Overview
Silent Language is a deliberately incomplete writing system. It encodes sentences as sequences of arbitrary non-linguistic symbols, each symbol cluster’s length corresponding to a word length. The system rejects stable meaning. Writers provide rhythm; readers hallucinate content. No reading is definitive. Every interpretation is ephemeral.

## Protocol
### Encoding (Writer)
- Each word is encoded by repeating a chosen non-linguistic symbol.
- Writers select any non-linguistic symbol for each word.
- The number of repetitions equals word length.
- Symbol choice carries no message.

Example:
```
Silent language fails beautifully
```
Could become:
```
◆◆◆◆◆◆ ✦✦✦✦✦✦✦✦ ➤➤➤➤ ✿✿✿✿✿✿✿✿✿✿
```

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
```
Writer output:
```
✶✶✶ ✦✦✦✦✦ ✪✪ ✧✧✧✧
```
Reader interpretation:
```
Own rhythm so cold
```

## Why LLMs?
- LLMs act as reflection engines.
- They never recover intended meaning.
- They generate from structure and bias.
- They demonstrate linguistic drift.
- Their outputs embody unpredictable projections.

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

