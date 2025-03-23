import json
import re
from datasets import load_dataset

def text_to_lengths(sentence):
    words = re.findall(r'\b\w+\b', sentence)
    return [len(word) for word in words]

# Use a smaller dataset (wikitext-2)
dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="train")

examples = []
idx = 1
NUM_EXAMPLES = 1000

for item in dataset:
    sentences = re.split(r'(?<=[.!?]) +', item['text'])
    for sentence in sentences:
        clean_sentence = sentence.strip()
        if 3 <= len(clean_sentence.split()) <= 12:
            lengths = text_to_lengths(clean_sentence)
            example = {
                "id": f"{idx:03}",
                "language": "English",
                "text": clean_sentence,
                "lengths": lengths
            }
            examples.append(example)
            idx += 1
            if idx > NUM_EXAMPLES:
                break
    if idx > NUM_EXAMPLES:
        break

final_dataset = {"examples": examples}

with open("dataset.json", "w", encoding="utf-8") as f:
    json.dump(final_dataset, f, indent=2, ensure_ascii=False)

print(f"{len(examples)} examples saved to dataset.json.")
