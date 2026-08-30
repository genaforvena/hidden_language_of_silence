import json
import re
from datasets import load_dataset

# The notation is silent.py's, imported rather than restated. It used to be a private
# SYMBOL list in this file, and that is how the training lane ended up learning a channel
# the repository had already replaced: the protocol moved to a single mark and this
# generator kept minting per-word symbol clusters for months. A second copy of a
# declaration drifts the day either side is fixed.
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from silent import encode as encode_silent  # noqa: E402


def text_to_shapes(sentence):
    """One run per word, one mark per letter. The channel is the lengths."""
    return encode_silent(" ".join(re.findall(r'\b\w+\b', sentence))).split(" ")


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
                "language": "silent-language",
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
