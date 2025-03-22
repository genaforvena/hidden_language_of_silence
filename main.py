
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as T
from torch.utils.data import Dataset, DataLoader
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import random
import string

# 1. Dataset generation: ghost-text creation
class GhostTextDataset(Dataset):
    def __init__(self, texts, img_size=(128, 128), font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        self.texts = texts
        self.img_size = img_size
        self.font = ImageFont.truetype(font_path, size=20)
        self.transforms = T.Compose([
            T.Resize(img_size),
            T.ToTensor(),
            T.GaussianBlur(kernel_size=5),
            T.RandomRotation(degrees=15),
            T.RandomPerspective(distortion_scale=0.5, p=0.7),
        ])

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        img = Image.new('L', (256, 64), color=255)
        draw = ImageDraw.Draw(img)
        draw.text((10, 20), text, font=self.font, fill=0)
        img = self.transforms(img)
        target = torch.tensor([ord(c) for c in text], dtype=torch.long)
        return img, target, text


# 2. Visual encoder backbone
class VisualEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(1)
        )

    def forward(self, x):
        x = self.conv(x)
        return x.view(x.size(0), -1)


# 3. Transformer-based decoder head
class TransformerDecoderHead(nn.Module):
    def __init__(self, embed_dim, vocab_size, num_layers=2, num_heads=4):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.decoder_layer = nn.TransformerDecoderLayer(d_model=embed_dim, nhead=num_heads)
        self.decoder = nn.TransformerDecoder(self.decoder_layer, num_layers=num_layers)
        self.fc_out = nn.Linear(embed_dim, vocab_size)

    def forward(self, memory, tgt):
        tgt_embed = self.embedding(tgt).transpose(0, 1)  # sequence-first
        memory = memory.unsqueeze(0)
        output = self.decoder(tgt_embed, memory)
        output = self.fc_out(output)
        return output.transpose(0, 1)


# 4. Model wrapper
class GhostLanguageModel(nn.Module):
    def __init__(self, vocab_size, embed_dim=256):
        super().__init__()
        self.encoder = VisualEncoder()
        self.decoder = TransformerDecoderHead(embed_dim, vocab_size)
        self.memory_proj = nn.Linear(128, embed_dim)

    def forward(self, img, tgt_seq):
        memory = self.encoder(img)
        memory = self.memory_proj(memory)
        output = self.decoder(memory, tgt_seq)
        return output


# 5. Generate random text and dataset
def generate_random_text(length=20):
    return ''.join(random.choices(string.ascii_lowercase + ' ', k=length))

texts = [generate_random_text() for _ in range(1000)]
dataset = GhostTextDataset(texts)
dataloader = DataLoader(dataset, batch_size=8, shuffle=True)

# 6. Training loop
vocab_size = 128
model = GhostLanguageModel(vocab_size=vocab_size)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

for epoch in range(3):
    model.train()
    for batch_idx, (imgs, targets, _) in enumerate(dataloader):
        imgs, targets = imgs.to(device), targets.to(device)
        optimizer.zero_grad()
        output = model(imgs, targets[:, :-1])
        loss = criterion(output.reshape(-1, vocab_size), targets[:, 1:].reshape(-1))
        loss.backward()
        optimizer.step()

        if batch_idx % 50 == 0:
            print(f"Epoch {epoch+1} Batch {batch_idx} Loss {loss.item():.4f}")

print("Training completed.")

# 7. Inference function to sample text from visual ghost input
def sample_inference(model, image, max_length=20, start_token=32):
    model.eval()
    with torch.no_grad():
        memory = model.encoder(image.unsqueeze(0).to(device))
        memory = model.memory_proj(memory)

        generated = [start_token]
        for _ in range(max_length):
            input_seq = torch.tensor(generated, dtype=torch.long).unsqueeze(0).to(device)
            output = model.decoder(memory, input_seq)
            next_char = output[0, -1].argmax().item()
            generated.append(next_char)
            if next_char == 32:  # stop at space
                break

    generated_text = ''.join(chr(c) for c in generated if c >= 32 and c < 127)
    return generated_text

# 8. Visualisation example
def visualize_inference(dataset, model, num_samples=3):
    fig, axes = plt.subplots(num_samples, 1, figsize=(8, num_samples * 3))
    for i in range(num_samples):
        img_tensor, _, original_text = dataset[i]
        gen_text = sample_inference(model, img_tensor)

        img_np = img_tensor.squeeze().numpy()
        axes[i].imshow(img_np, cmap='gray')
        axes[i].set_title(f'Original: {original_text}\nGenerated: {gen_text}')
        axes[i].axis('off')

    plt.tight_layout()
    plt.show()

# Example call after training:
# visualize_inference(dataset, model)
