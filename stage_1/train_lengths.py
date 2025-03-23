
import json
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Trainer, TrainingArguments

# Load dataset
with open("shape-dataset.json", "r") as f:
    data = json.load(f)["examples"]

inputs = ["translate lengths to sentence: " + " ".join(map(str, item["lengths"])) for item in data]
targets = [item["text"] for item in data]

dataset = Dataset.from_dict({"input": inputs, "target": targets})

# Tokenizer & Model
tokenizer = AutoTokenizer.from_pretrained("t5-small")
model = AutoModelForSeq2SeqLM.from_pretrained("t5-small")

def preprocess(batch):
    inputs = tokenizer(batch["input"], padding="max_length", truncation=True, max_length=32)
    targets = tokenizer(batch["target"], padding="max_length", truncation=True, max_length=32)
    inputs["labels"] = targets["input_ids"]
    return inputs

dataset = dataset.map(preprocess, batched=True, remove_columns=["input", "target"])

# Training
args = TrainingArguments(
    output_dir="./length-model",
    num_train_epochs=20,
    per_device_train_batch_size=4,
    learning_rate=5e-5,
    logging_steps=10,
    save_steps=20,
    evaluation_strategy="no"
)

trainer = Trainer(model=model, args=args, train_dataset=dataset)
trainer.train()

model.save_pretrained("./length-model-final")
tokenizer.save_pretrained("./length-model-final")
