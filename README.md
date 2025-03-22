# Spectral Language Inference: Toward Pre-Semiotic Language Modeling — Research Proposal

## Abstract
Current language models rely on discrete symbolic representations: characters, tokens, subwords, or bytes. Even byte-level models process input as a sequence of discrete signifiers. This research proposes a radical departure: to train models on the visual ghost-structures of text without direct symbolic presence.

## Research Question
Can semantic or syntactic structure emerge from non-symbolic, spatial visual patterns—ghosts of text—absent any recognisable symbols?

## Hypothesis
Language encodes structure not only in lexical tokens but in distributional geometry: visual patterns that reflect frequency, cadence, spatial alignment, and repetition. These pre-symbolic structures may carry latent linguistic signals sufficient for prediction, reconstruction, or plausible interpretation.

## Proposed Methodology

### 1. Dataset Preparation
- Generate synthetic datasets where text is rasterised into images and transformed into ghost-like distortions.
- Remove all possibility of OCR decoding by using blurs, random rotations, perspective warps, edge detection, and resolution reduction.
- Store original paired text for supervised objectives and semantic inference tasks.

### 2. Model Architecture
- **Visual Encoder:** A convolutional neural network (CNN) to process spatial structures.
- **Hierarchical Transformer Attention:** Vision Transformer layers to model long-range spatial dependencies.
- **Transformer Decoder Head:** To predict either text sequences or latent embeddings.
- Optionally incorporate masked autoencoder (MAE) pretraining.

### 3. Training Strategy
- Pre-train the encoder-decoder model on ghost-text reconstruction.
- Fine-tune for semantic prediction with paired visual-lexical data.
- Implement contrastive learning objectives, similar to CLIP, but with text replaced by ghost-structures.

### 4. Evaluation Metrics
- **Reconstruction Accuracy:** Compare generated sequences with ground truth.
- **Semantic Plausibility:** Use embedding distance metrics to measure plausibility.
- **Decipherment Tests:** Attempt to map ghost-text to unseen linguistic patterns.
- **Adversarial Decoding:** Test the model’s robustness against random distortions.

## Applications
- Deciphering unknown scripts without symbol dictionaries.
- Cryptographic inference.
- Cognitive modeling of pre-linguistic visual perception in early childhood.
- Testing the boundaries of the distributional hypothesis beyond lexical units.
- Generative visual poetry.

## Why Hasn’t This Been Done Before?
- The dominance of symbolic models in NLP.
- Lack of interdisciplinary convergence between computer vision, cognitive science, and ancient script analysis.
- Absence of large-scale datasets for ghost-text modeling.
- Prevailing assumptions that symbolic representation is the only gateway to meaning.

## Why Now?
- Availability of vision transformers and self-supervised learning frameworks.
- A shift toward pattern-based inference models (SimCLR, BYOL, DINO).
- Increasing interest in the decipherment of lost languages and scripts.
- Advancements in computational cognitive modeling.

## Further Reading
- Friston, K. (2010). The free-energy principle.
- Bouchard-Côté et al. (2013). Unsupervised decipherment of lost languages.
- Seidenberg & McClelland (1989). A distributed, developmental model of word recognition and naming.
- Radford et al. (2021). Learning Transferable Visual Models From Natural Language Supervision.

WDYT?
