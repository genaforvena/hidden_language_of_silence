import time
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("./length-model-final")
model = AutoModelForSeq2SeqLM.from_pretrained("./length-model-final")

def infer(length_sequence):
    input_str = "translate lengths to sentence: " + " ".join(map(str, length_sequence))
    inputs = tokenizer.encode(input_str, return_tensors="pt")
    outputs = model.generate(inputs, max_length=32, num_beams=5, early_stopping=True)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Length sequences to test periodically
test_sequences = [
    [4, 5, 4],
    [3, 3, 5, 3],
    [3, 3, 4, 6],
]

# Run inference every 10 minutes
interval_seconds = 600  # 600 seconds = 10 minutes

while True:
    print(f"\n--- Inference run at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    for seq in test_sequences:
        result = infer(seq)
        print(f"Lengths: {seq} → Sentence: {result}")
    time.sleep(interval_seconds)
