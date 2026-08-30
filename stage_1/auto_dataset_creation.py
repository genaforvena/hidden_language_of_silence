import json
import re
from datasets import load_dataset

# The protocol says the symbol carries no message and is chosen at random.
# The old SYMBOL_MAP broke that in two ways at once:
#   1. it keyed the symbol on the WORD LENGTH, so the symbol restated the one thing the
#      channel is supposed to be -- a reader could recover length from the glyph alone,
#      without counting. That is a side channel in a project whose whole claim is that
#      length is the only channel.
#   2. it was not even injective: 3 and 9 both mapped to '*', so the side channel was
#      also ambiguous.
# Symbols are now drawn at random per word, independent of length, and pinned to TEXT
# presentation (U+FE0E) so no font renders one as a double-width colour emoji and eats
# the space between clusters.
import random

TEXT = "\uFE0E"
SYMBOLS = [c + TEXT for c in "\u25FC\u25C6\u2726\u2794\u2756\u23C3\u25B3\u2A3F\u25C7\u25BD"]

def text_to_shapes(sentence):
    words = re.findall(r'\b\w+\b', sentence)
    return [random.choice(SYMBOLS) * len(word) for word in words]

# Load smaller dataset
print("Loading dataset...")
dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="train")

examples = []
idx = 1
NUM_EXAMPLES = 1000

for item in dataset:
    sentences = re.split(r'(?<=[.!?]) +', item['text'])
    for sentence in sentences:
        clean_sentence = sentence.strip()
        if "=" in clean_sentence:
            continue
        if 3 <= len(clean_sentence.split()) <= 12:
            shapes = text_to_shapes(clean_sentence)
            example = {
                "id": f"{idx:03}",
                "language": "abstract-silence",
                "shape": " ".join(shapes),
                "text": clean_sentence
            }
            examples.append(example)
            idx = idx + 1
        if idx > NUM_EXAMPLES:
            break
    if idx > NUM_EXAMPLES:
        break

final_dataset = {"examples": examples}

with open("shape_dataset.json", "w", encoding="utf-8") as f:
    json.dump(final_dataset, f, indent=2, ensure_ascii=False)

print(f"{len(examples)} examples saved to shape_dataset.json.")
