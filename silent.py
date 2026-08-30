#!/usr/bin/env python3
"""The silent channel: a sentence goes out as its word lengths and nothing else.

    "The night is long"  ->  "▁▁▁ ▁▁▁▁▁ ▁▁ ▁▁▁▁"  ->  [3, 5, 2, 4]

One mark, repeated once per letter. Words separated by a space. Nothing else exists.

The writer is given NO choice, and that is the whole design. Earlier versions let the
writer pick a fresh symbol per word, and a free choice is a side channel: it can restate
the length, or carry a picture -- U+2601 CLOUD and U+2717 BALLOT X were struck from that
set for exactly that. With one mark there is nothing to choose and nothing to smuggle.

WHY THIS MARK AND NOT AN ASCII UNDERSCORE. Measured, not preferred -- see
measure/transport.py and measure/result-transport.json:

    ___ _____ __ ____        markdown ->  <hr>

A line made only of underscores and spaces is a horizontal rule. On GitHub, in a README,
in any markdown chat, the message does not arrive as a different message: it does not
arrive at all. (Append a full stop and it survives, which is worse -- a protocol that
depends on remembering punctuation is not a protocol.) U+2581 LOWER ONE EIGHTH BLOCK
looks like the underscore, joins into a continuous low line when repeated, is ordinary
text to every markdown parser, and does not collapse in a browser. Same picture, no
asterisk.

The separator must differ from the mark, and a space does. Were both the same, 6 + gap +
8 would be fourteen marks in a row and one fourteen-letter word could not be told from
two. That is not a legibility problem; the channel stops being decodable.

The channel is the LENGTHS. measure/ceiling.py says what that is worth: 3.42 bits per
word against the word's 11.72, so a reader supplies ~8.42 bits -- about 343 equiprobable
words per slot. No reading is a decoding, because the sentence was never sent.
"""

MARK = "▁"        # U+2581. One line changes the notation; nothing else in the repo knows.
WORD_SEP = " "


def encode(sentence: str) -> str:
    """'The night is long' -> '▁▁▁ ▁▁▁▁▁ ▁▁ ▁▁▁▁'."""
    return WORD_SEP.join(MARK * len(w) for w in sentence.split())


def lengths(encoded: str) -> list[int]:
    """The only thing the channel carries: one length per word."""
    return [len(chunk) for chunk in encoded.split(WORD_SEP) if chunk]


if __name__ == "__main__":
    import sys
    text = " ".join(sys.argv[1:]) or "The night is long"
    enc = encode(text)
    print("input:   ", text)
    print("encoded: ", enc)
    print("lengths: ", lengths(enc))
