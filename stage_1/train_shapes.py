
import json
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, DataCollatorForSeq2Seq, TrainingArguments, Trainer
from transformers import T5ForConditionalGeneration, T5Tokenizer

# Load dataset from the generated JSON
with open("shape_dataset.json", "r", encoding="utf-8") as f:
    data_json = json.load(f)

# Convert to Hugging Face dataset format
examples = data_json["examples"]
print("Loaded examples. First: " + str(examples[0]))
data = Dataset.from_list([
    {
        "input_text": item["shape"],
        "target_text": item["text"]
    }
    for item in examples
])

# Load tokenizer and model (use T5 small or base depending on compute)
model_name = "t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

# Tokenize
def tokenize_function(examples):
    model_inputs = tokenizer(
        examples["input_text"],
        max_length=64,
        padding="max_length",
        truncation=True,
    )
    labels = tokenizer(
        examples["target_text"],
        max_length=64,
        padding="max_length",
        truncation=True,
    )
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

tokenized_data = data.map(tokenize_function, batched=True, remove_columns=["input_text", "target_text"])

# Data collator
data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

# Training arguments
training_args = TrainingArguments(
    output_dir="./shape-model-checkpoints",
    evaluation_strategy="no",
    learning_rate=5e-5,
    per_device_train_batch_size=8,
    num_train_epochs=15,
    weight_decay=0.01,
    save_steps=500,
    save_total_limit=2,
    logging_steps=50,
    logging_dir="./logs",
    report_to="none"
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_data,
    data_collator=data_collator,
    tokenizer=tokenizer,
)

# Train
trainer.train()

# Save final model
trainer.save_model("./shape-model-final")
tokenizer.save_pretrained("./shape-model-final")

print("Training complete and model saved to ./shape-model-final")
