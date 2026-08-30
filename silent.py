#!/usr/bin/env python3
"""The silent channel: a word is a run of SPACES, one per letter.

The encoded message is made entirely of whitespace. There is nothing to look at --
that is the point, and it is what the project's name always claimed.

Word separator is TAB, and it has to be something other than a space. If both the
letters and the gaps were spaces, "6 + gap + 8" would be fifteen spaces in a row and
a reader could not tell one fifteen-letter word from two words. The channel would
stop being decodable at all, which is a different thing from being hard to read.
"""

WORD_SEP = "\t"
LETTER = " "


def encode(sentence: str) -> str:
    """'The night is long' -> '   \t     \t  \t    ' (whitespace only)."""
    return WORD_SEP.join(LETTER * len(w) for w in sentence.split())


def lengths(encoded: str) -> list[int]:
    """The only thing the channel carries: one length per word."""
    return [len(chunk) for chunk in encoded.split(WORD_SEP)]


def visible(encoded: str, dot: str = "·") -> str:
    """A DEBUG rendering. Never the channel itself -- a visible stand-in for a space
    is a symbol again, and symbols are what this encoding exists to remove."""
    return WORD_SEP.join(dot * n for n in lengths(encoded))


if __name__ == "__main__":
    import sys
    text = " ".join(sys.argv[1:]) or "The night is long"
    enc = encode(text)
    print("input:    ", text)
    print("lengths:  ", lengths(enc))
    print("visible:  ", visible(enc))
    print("encoded:  ", repr(enc))
