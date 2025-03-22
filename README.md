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


# Discussion: Is Replacing Words with Uniform Black Blocks a Good Idea?

## Arguments For

### 1. Purity of Rhythm
- Stripping text down to uniform blocks forces the model (and human reader) to rely purely on spacing, cadence, and distribution.
- It highlights syntax as rhythm rather than symbol.

### 2. Minimalist Encoding
- Could serve as the most extreme form of information compression: conveying structure through geometry alone.
- Useful for encryption, secret messaging, and steganography.

### 3. Cognitive Echoes
- Infants first perceive speech as undifferentiated sound rhythms; this mimics that pre-symbolic stage.
- Aligns with theories that syntax and structure precede lexical mapping.

### 4. Testing Limits of the Distributional Hypothesis
- Challenges whether word order and spacing alone can carry latent meaning.
- If models succeed, this questions whether linguistic meaning truly resides in symbols or just in arrangements.

## Arguments Against

### 1. Loss of Complexity
- Uniform blocks remove phonetic and morphological hints.
- Reduces information to spacing and length, which may be too sparse.

### 2. Ambiguity Overload
- Different sentences may map to nearly identical block structures.
- Risk of irrecoverable collisions.

### 3. Symbolic Dependence in Language Evolution
- Written language evolved specifically to overcome ambiguity by encoding phonemic information.
- Stripping this away might fight evolutionary design rather than test it.

### 4. Computational Traps
- Models might only learn trivial statistics (average spacing between punctuation) rather than deep inference.

## Contrarian Take
- The very point might be the failure: to show that beyond a certain point, geometry collapses.
- Such collapse could reveal where language stops and noise begins.
- Might generate unexpected poetry, randomness-as-meaning.

## Conclusion?
- Worth doing for failure.
- Worth doing for the silence it might produce.
- If it works, it’s profound. If it doesn’t, the collapse itself is data.

## Potential Outcomes

### Success Scenario
- The model learns to infer structure, grammar, and even semantic cues purely from spacing and block rhythm.
- The emergence of latent syntactic rules without lexical hints.
- Potential to create new visual forms of poetry and cryptic writing.

### Partial Success
- The model can differentiate sentence types and punctuation usage.
- Good performance on short structures; collapse with longer, complex text.
- Evidence of rhythm-based parsing capabilities.

### Failure Scenario
- Output degenerates into random prediction noise.
- The model overfits trivial cues (length, punctuation frequency) and fails to generalise.
- Provides strong evidence that symbols are required for sustained complexity.

## Risks
- Model collapse might waste compute resources.
- Difficulty in interpreting partial successes; could lead to ambiguous conclusions.
- Temptation to retrofit explanations for model noise.
- Possible dead-end unless reframed as artistic or cognitive research.

## Experiment Protocols

### 1. Dataset Generation
- Create pairs of normal text and black-block text with the same structure.
- Generate varying complexity levels: simple phrases, full sentences, and paragraphs.
- Ensure balance across different languages and syntactic structures.

### 2. Training Process
- Train a visual transformer-based model to predict original text from black-block sequences.
- Use contrastive learning to enforce separability between distinct structures.
- Evaluate zero-shot inference capabilities on unseen text formats.

### 3. Evaluation Methods
- **Accuracy Tests:** Measure reconstruction success rate against ground truth.
- **Latent Structure Analysis:** Check if embedding space preserves syntactic relationships.
- **Failure Mode Analysis:** Examine when and how the model collapses.

### 4. Control Comparisons
- Compare performance against traditional symbol-based language models.
- Test with and without punctuation to isolate rhythm vs. syntactic dependencies.

## Further Reading
- Friston, K. (2010). The free-energy principle.
- Bouchard-Côté et al. (2013). Unsupervised decipherment of lost languages.
- Seidenberg & McClelland (1989). A distributed, developmental model of word recognition and naming.
- Radford et al. (2021). Learning Transferable Visual Models From Natural Language Supervision.

