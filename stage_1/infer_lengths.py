from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("./length-model-final")
model = AutoModelForSeq2SeqLM.from_pretrained("./length-model-final")

def infer(length_sequence):
    input_str = "translate lengths to sentence: " + " ".join(map(str, length_sequence))
    inputs = tokenizer.encode(input_str, return_tensors="pt")
    
    outputs = model.generate(
        inputs, 
        max_length=32, 
        num_beams=5,
        early_stopping=True,
        no_repeat_ngram_size=2
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Example inference
lengths = [4, 5, 4]
print("Lengths:", lengths)
print("Reconstructed:", infer(lengths))
