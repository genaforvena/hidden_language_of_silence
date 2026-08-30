# Covert use, and what the ceiling measurement does to it

*(Was `ENCRYPION_USECASE.md`, misspelled since it was written, and written against the
symbol protocol that no longer exists. The idea survives; three of its claims do not.)*

## What the channel is

A line of dot-runs, one run per word, one dot per letter. An observer sees a list of word
lengths. There is no ciphertext, no noise, and nothing that looks like a key.

## Where the covert capacity actually lives

Not in the marks. **`measure/ceiling.py` puts a number on it:** a word's length carries
3.30 bits, a word carries 11.28, so a reader supplies ~7.99 bits per word — about 253
equiprobable words per slot. That residual is the entire covert budget, and it belongs to
the **shared interpretive key**, never to the transmission.

So the honest framing is the inverse of the original one. The channel does not hide a
message; it hides *how much of the message was never sent*. Two parties with a shared
rule ("all four-letter words are nautical terms", "read the lengths as page numbers into
an agreed book") reconstruct from the key, and the line on the wire constrains them only
to a word-length skeleton.

## Three claims from the original that the measurement kills

1. **"Symbol-specific dictionaries — the symbol itself selects the dictionary."** Dead,
   and it was always a contradiction: the protocol's central rule is that the mark
   carries no message. There is now exactly one mark, so there is nothing to key on. If
   you want a per-word selector you must send it, and then you are no longer using this
   channel.
2. **"Interception and decoding by outsiders is effectively impossible."** Backwards. The
   channel is *weak*, not strong: an outsider reconstructing "some plausible sentence"
   succeeds trivially, because ~253 words fit each slot and most of them read fine. What
   an outsider cannot get is the key — and that is a statement about the key, not about
   this encoding. Do not call it cryptography; it has no primitive.
3. **"Vary symbol choices and lengths creatively."** Varying LENGTHS is varying the
   message: the lengths are the entire channel. The advice, written for a protocol where
   symbols were free, transferred to one where they are not.

## What still stands

- **Plausible deniability is real and is the actual property.** A dot skeleton is
  publishable as art, and is art. There is no step at which it looks like traffic.
- **The reader may be an LLM handed a private prompt.** Outsiders running the same model
  without the prompt get divergent readings — measured, not assumed:
  `measure/silent_channel.py` found readings of one length sequence converging no closer
  to the intended text than to a prior control.
- **Key rotation still matters**, for the ordinary reason: reuse across many messages
  leaks the mapping, and here the skeleton is public by construction.

## The risk nobody wrote down

The length sequence is not a nothing. 3.30 bits per word is small, but it is not zero,
and it is *stable across every message you ever send*. A traffic analyst does not need to
read you; they need to notice that your dot lines have a distribution, and word-length
distributions differ by language, register and author. If this is ever used for something
that matters, that — not the marks — is the leak.
