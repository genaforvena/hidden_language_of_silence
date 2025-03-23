import json
import re
from datasets import load_dataset

# Define a symbol mapping for lengths (up to length 12)
SYMBOL_MAP = {
    1: '@',
    2: '#',
    3: '$',
    4: '%',
    5: '&',
    6: '*',
    7: '+',
    8: '°',
    9: '*',
}

def text_to_shapes(sentence):
    words = re.findall(r'\b\w+\b', sentence)
    return [SYMBOL_MAP.get(len(word), '^') * len(word) for word in words]

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
