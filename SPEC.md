# The Silent Language Protocol (Minimal Spec)

## Overview:
This protocol describes a minimal symbolic language designed explicitly for encoding word lengths from natural language sentences. The encoding contains no semantic, lexical, or grammatical information. Interpretation (decoding) is deliberately open-ended and context-dependent.

---

## Encoding Rules:

- **Symbol Definition:**
  - Each word is encoded as a cluster of identical symbols. (Recommended default: ◼)
  
- **Word Encoding:**
  - Words are represented by repeated symbols equal to their character length:
    - Example: "dog" → ◼◼◼

- **Sentence Encoding:**
  - Spaces separate encoded words:
    - Example sentence: "the quick fox"
    - Encoded: ◼◼◼ ◼◼◼◼◼ ◼◼◼

- **Punctuation and Special Characters:**
  - Explicitly omitted from encoding by default.
  - Optional: May encode punctuation as isolated symbols (e.g., punctuation → ◆).

- **Capitalisation and Formatting:**
  - Explicitly not encoded.

---

## Decoding Rules (Constraints for Readers):

- **Word-Length Constraint:**
  - Decoded word must strictly match encoded length.

- **Local Coherence Constraint:**
  - Decoded word must fit coherently within immediate surrounding context (explicitly subjective).

- **Global Coherence:**
  - Explicitly secondary and non-essential.

- **Diversity Encouraged:**
  - Readers explicitly encouraged to maximise vocabulary diversity within constraints.

---

## Implementation Guidelines:

- **Open-ended Implementation:**
  - Any capable model or reader (LLM, human, or algorithmic) may implement decoding.

- **Prompt Recommendation for LLMs:**
  ```
  You will read sequences of symbols representing word lengths. Each word's length matches exactly the number of symbols.

  Example:
  ◼◼◼ ◼◼◼◼ ◼◼◼◼◼
  "the moon rises"

  Decode the following sequence. Prioritise local coherence. Maximise vocabulary diversity.
  ```

---

## Recommended Applications:

- Generative reading interfaces
- Interpretive installations
- Experimental literary and linguistic research

---

## Extensibility:

- **Optional Extensions:**
  - Private keys (interpretative conventions)
  - Structural ambiguities or irregularities

---

## Status:

- Minimal and open specification explicitly designed for experimentation, diversity, and creative interpretation.
- Protocol stability is ensured by strict encoding rules.
- Interpretative freedom explicitly encouraged at decoding stage.

