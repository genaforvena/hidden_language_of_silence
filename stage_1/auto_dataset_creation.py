
import json
import re
from datasets import load_dataset

def text_to_lengths(sentence):
    words = re.findall(r'\b\w+\b', sentence)
    return [len(word) for word in words]

# Load dataset (Wikipedia English)
dataset = load_dataset("wikipedia", "20220301.en", split="train[:1%]")

examples = []
idx = 1

for item in dataset:
    sentences = re.split(r'(?<=[.!?]) +', item['text'])
    for sentence in sentences:
        clean_sentence = sentence.strip()
        if len(clean_sentence.split()) >= 3 and len(clean_sentence.split()) <= 12:
            lengths = text_to_lengths(clean_sentence)
            example = {
                "id": f"{idx:03}",
                "language": "English",
                "text": clean_sentence,
                "lengths": lengths
            }
            examples.append(example)
            idx += 1
            if idx > 100:
                break
    if idx > 100:
        break

final_dataset = {"examples": examples}

# Save to JSON
with open("dataset.json", "w", encoding="utf-8") as f:
    json.dump(final_dataset, f, indent=2, ensure_ascii=False)

print(f"{len(examples)} examples saved to dataset.json.")
