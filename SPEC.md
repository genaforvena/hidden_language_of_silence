## The Silent Language System Spec

### Protocol

**Encoding (Writer):**
- Each word is represented by a repeated sequence of a single non-linguistic symbol.
- The symbol is chosen freely by the writer for each word; it can differ every time.
- The number of repetitions equals the length of the word.
- No restrictions on the choice of symbol other than that it cannot be part of an existing linguistic system.
- Example: The sentence “silent languages fail” can become:
```
◆◆◆◆◆◆ ✦✦✦✦✦✦✦✦ ➤➤➤➤
```
or:
```
◼◼◼◼◼◼◼ ✖✖✖✖✖✖✖✖ ✿✿✿✿
```
Both are valid encodings.

**Decoding (Reader):**
- Decoding relies on counting the length of each cluster.
- The choice of symbol carries zero interpretative weight.
- The reader generates coherent text by matching each cluster’s length with words, guided only by length and local coherence.
- Reader systems may be language models, humans, or any generative mechanism.

**Re-encoding cycle:**
- The resulting reading can be encoded again into a fresh symbolic form by a writer.
- No stability or repetition of symbols is required.
