# Does the silent channel carry anything?

The project README asserts that LLM readers "never recover intended meaning."
It is the most interesting claim in this repository and it had never been
measured. This directory measures it.

## What the channel actually carries

Encoding maps each word to a cluster of a freely chosen symbol, repeated
word-length times, and the spec is explicit that symbol choice carries no
message. So the entire channel is the **length sequence** `L = [l1..ln]`.
Nothing else survives encoding. Whatever a reader recovers must come from `L`
plus the reader's own prior — and separating those two is the whole problem.

## The design

Encode a known text, take **N independent readings** (separate processes, no
shared context — a single sampled list is not N readings), and measure how much
the readings agree **with each other**, against an explicit random basis at
**the same lengths and the same alphabet**.

| arm | what it is | what it isolates |
|---|---|---|
| **A** treatment | N readings of the true message's `L` | channel + prior |
| **B** prior control | N readings of a *different* `L'` — same word count, lengths resampled from the same distribution | the prior and the task framing alone, with no particular message behind it |
| **C** random basis | N texts assembled with **no model**: a random word of the right length at each position | the chance floor |

Three agreement metrics, all pairwise within an arm: **positional** (do two
readings pick the same word at the same slot — well defined because every text
in an arm shares a length profile), **Jaccard** over word bags, and **cosine**
over sentence embeddings.

**Recovery is asked separately from convergence.** They are different claims:
readings can agree with each other while all being wrong. So each arm-A reading is
compared to the *true* original — and the comparison that decides is against **arm
B**, which read a different length sequence and never saw this message. Matched-length
decoys and arm C are also scored, as chance floors for context. They are not the test;
see "The recovery arm had the wrong floor" below, which is the main finding of this
directory.

## Two things that will quietly ruin this measurement

**A basis pooled from too few texts is not a floor.** The first version drew arm
C's alphabet from arm B's readings alone. With 7 valid control readings the
vocabulary is so small that the "random" texts are near-duplicates of each
other, and the floor rises to meet the thing it is supposed to sit under —
measured, that inflated the semantic floor to **cosine 0.391, above the model
readings at 0.232**. The alphabet is now requested independently of any message
and merged with the control arm's words; the run prints which source it used and
says so in the artifact when it has to fall back.

**Agreement above chance requires the chance arm to share the lengths AND the
alphabet.** Drop either and the number measures the model's prior instead of the
channel. That is why arm C is length-matched and drawn from the reader's own
vocabulary rather than from a dictionary the model would never use.

Pairwise similarities share texts, so they are not independent; the bootstrap
interval is descriptive, and the argument is carried by arm-against-arm on the
same construction, never by one arm's interval alone.

## A third thing, and it already bit this measurement

**A result file that cannot name the instrument that wrote it is not evidence.**

`result-msg2.json` — the replication that *reverses* the headline of run 1 — was
written at 03:28:14Z by a process launched before the 03:24:31Z commit that added
the per-position breakdown. Python reads its source once, at start: that run
executed the old code to completion and its output came from an instrument that
no longer exists in the tree. Nothing in the file said so. The only trace was a
**missing key**, which is the weakest possible signal and reads exactly like a run
that had nothing to report.

Every artifact now carries a `provenance` block, and the stamp is taken **twice**:

- `at_start` — taken at import, before anything runs. This is what actually
  produced the numbers. A stamp taken only at write time would have recorded the
  commit that was *not* running.
- `at_write` — the tree as it stands when the file lands.
- `changed_mid_run` — names the fields that moved between them, so a mid-run edit
  is *asserted* rather than inferred from an absence.

Each field fails to a string beginning `unknown:` naming which probe failed; a
provenance field that quietly reports a plausible default is worse than none.

### What the field must NOT key on, learned from its own first run

`changed_mid_run` keys on the **instrument's own bytes** (`script_sha256`,
`instrument_dirty`) and never on `git_head`. HEAD is a property of the *tree*: any
commit anywhere in the repo moves it, so on a run of any length it fires almost
always, the field goes permanently true, and a real instrument change then rides in
under exactly that suppression.

This was measured, not reasoned about, and the artifacts in this directory are the
evidence. Both re-runs were launched at `21f344b`; committing the *test file* as
`79594e1` mid-run moved HEAD while
`git rev-parse 21f344b:measure/silent_channel.py` and `79594e1:…` are the same blob
`a1c4c8a8`. `result-msg1-stamped.json` therefore carries
`changed_mid_run: ["git_head"]` and the sentence "the instrument changed under this
run" — **which is false, and it is left in place on purpose.** Its own
`at_start.script_sha256` is `16f716c8…`, which names the pre-fix instrument, so a
reader can date the verdict and disregard it. That is the feature working on itself:
a wrong derived field stays interpretable because the raw stamp under it is intact,
which is why both halves are kept rather than only the verdict.

The arm that would have caught this did not exist, because the only mutation ever
driven was the one that edits the instrument itself — the test could confirm the
alarm but never bound it. `test_provenance.py` now drives both directions.

## Recovery, measured at last — and the answer is no

Convergence is model-free and always lands. Recovery needs an embedding backend, and
both re-runs hit an ollama mid-upgrade: every `/api/embeddings` returned HTTP 500
because the `llama-server` binary had been removed before its replacement arrived. The
artifacts carried `cosine: null` and no `recovery` block — the harness said so instead
of writing a plausible number. That is the correct behaviour and it is why the numbers
below exist at all: `recover_recompute.py` computes the block from the stored readings
once a backend returns, with no new model calls, tagged with its own provenance so the
file still says which instrument produced which number.

The backend came back on 2026-08-30 and both artifacts were recomputed. **The README's
central claim survives.** Readings of the true length sequence are no nearer the
intended message than readings of a *different* length sequence by the same model.

| | msg1 "The night is long…" | msg2 "Rain fell across…" |
|---|---|---|
| A treatment → true | 0.2402 | 0.1122 |
| **B prior control → true** | **0.2199** | **0.1240** |
| C random basis → true | 0.1594 | 0.1160 |
| matched decoys | 0.1531 | 0.1934 |
| **A − B_prior** | **+0.0203, CI [−0.0453, +0.0835]** | **−0.0118, CI [−0.0516, +0.0270]** |

Both intervals contain 0. n=20 readings per arm, cosine over `all-minilm`.

## The recovery arm had the wrong floor, and the wrong floor manufactured a result

This is the finding, and it is the same mistake this directory already documents for
the *convergence* arm, made one ring out.

The arm originally scored arm-A readings against **length-matched decoys** and called
beating them recovery. A decoy is random words at the right lengths. Any fluent English
sentence about a plausible scene beats it — having recovered nothing. Measured: on msg1
the decoy floor is **0.153** and the model-free arm C is **0.159**, the same number. The
decoy floor was a *chance* floor wearing a *prior* floor's name.

Arm B is the floor that decides: real readings, same model, same framing, of a length
sequence that is not this message's. It sits at **0.220** — two thirds of the way from
the chance floor to the treatment arm. Against chance, msg1 reads as recovery
(A − C = +0.0808, CI [+0.0287, +0.1321], excludes 0). Against the prior, the whole
effect is gone.

**The old floor also made the two messages appear to disagree**, which is worse than a
wrong number because it invites picking one. Under the decoy floor msg1 read "recovery"
(0.240 > 0.153) and msg2 read "no recovery" (0.112 < 0.193), and a reader would quote
whichever suited. Under the prior floor both say the same thing.

Two things were checked before blaming the floor, and one of them refuted the first
guess:

- **The decoy draw is not the free parameter.** `to_decoy` was recomputed over 24
  independent decoy draws, and again over draws from half the pool: sd 0.012–0.026, and
  the verdict was 24/24 stable in *both* directions. The floor is stable; it is
  measuring the wrong thing.
- **The post-hoc pool was not the run's own.** `recover_recompute.py` rebuilt the decoy
  alphabet from texts C+B, because artifacts stored only the **size** of the run's basis
  alphabet. That proxy is a strict subset — 163 of 303 words on msg1, 187 of 337 on
  msg2. It did not change the verdict here (previous point), but a floor drawn from half
  the alphabet is a different measurement wearing the same field name. Runs now store
  the lexicon itself; on an older artifact the script falls back to the proxy and
  **names it in the block**.

### Two copies of the scoring code, already drifted

The fix is also a de-duplication, and the duplication had already cost something. The
inline arm and the post-hoc recompute were separate implementations of the same
scoring, and the recompute shipped **bare means with no intervals** where the inline
arm shipped means with intervals — so two files in this directory carried the same
field name under two different standards of evidence, and the weaker one carried the
headline. Scoring now lives in exactly one place, `silent_channel.recovery_block()`,
which both call.

### A blind arm was wearing a verdict, and the failure direction was the bad one

Found by the first live drive of the fixed code, not by the unit tests — every fixture
had readings in every arm. At `-n 6` the reader missed the length profile on **all six**
control readings (`compliance.B.valid: 0`), so the prior arm was `n=0`. The block still
printed **"NO recovery above the prior (A − B_prior includes 0)"**: a claim about an
interval that does not exist.

That is the worst possible direction for it to fail. No-recovery is also the *true*
answer, so a completely blind run agrees with the real ones and cannot be told apart
from them — a run that measured nothing would have corroborated the finding above.
An empty treatment or prior arm now renders `UNKNOWN` naming which arm is missing, and
`excludes_zero` is `None` rather than `False`, because `False` is a measured negative.
The other arms still report their own numbers; only the verdict abstains.

`test_recovery.py` covers it with 14 mutants driven red against a green control,
including the original bug (verdict keyed on the decoy floor), the recompute's missing
intervals, a one-sample difference interval, and each half of the blindness guard. Its fixture had to be fixed twice
before it could discriminate: a single-bucket lexicon cannot tell a length-matched decoy
from an unmatched one, and two identical arms give a zero-width interval that contains 0
for free — an arm that cannot fail.

## The recovery numbers are similarities, not distances

`recovery.to_true`, `to_prior`, `to_chance` and `to_decoy` are **cosine similarities:
higher means closer.** "The readings sit 0.210 from the true original" inverts the
direction and is the sentence a reader will quote, so the artifact carries `metric`,
`direction` and `reading` fields spelling it out. The no-recovery result is
`A_minus_prior.ci` containing 0 — not `to_decoy >= to_true`, which was the old and
wrong test.

## Running it

```bash
python3 measure/silent_channel.py --text "your known message" -n 20
```

Needs a reader command taking a prompt as `argv[1]` and printing the reply
(`--relay`, default `mesh-relay`), and any embedding endpoint for the semantic
metric (`--no-embed` to skip). Every reading, arm and pair lands in the JSON
artifact so the numbers can be recomputed without re-running the models.

---

# The ceiling: how much can the channel carry at all?

`silent_channel.py` asked whether readers recover the message and answered **no**.
That is a result about two messages, one reader family, one framing — and it leaves
the obvious question unasked. `ceiling.py` asks it, and needs **no model at all**:

> A word's shape is its length. How many bits is that, against how many bits a word
> carries?

Measured on **wikitext-103** (the corpus `stage_1/` trains on), 6.89M tokens inside
the 3–12-word sentence window, 761,273 distinct sentences, `[A-Za-z']+` tokenisation:

| quantity | bits | what it is |
|---|---:|---|
| **H(length)** | **3.30** | hard ceiling on the channel, per word |
| H(word) | 11.28 | what a word carries, unigram |
| **H(word \| length)** | **7.99** | **what the RECEIVER must supply** |
| I(word; length) | 3.30 | what the shape actually delivers = **29.2%** of the word |

**253 words fit each slot.** Not 253 plausible ones — 253 *equiprobable* ones, which
is what 7.99 residual bits means. A ten-word sentence therefore leaves ~80 bits for
the receiver to supply: about 10²⁴ word-sequences match the shape, under an
independence assumption that only ever *overstates* the count.

That figure is a **size, not a verdict**. It is how big the admissible set is, and the
word for it depends on what you want from the channel: difficulty if you mean to recover
the original, room if you mean to invent one. This project says reading is invention, so
on its own terms a wider slot is richer rather than worse. Both readings are correct and
neither is named here as the true one.

So the null result is not a failure of the readers. **It is the prediction.** Two
readers handed the same shape are choosing inside the same 253-wide slot with the
same prior, and that is precisely what the prior-control arm found them doing.

## Where the estimate is solid and where it is not

**Converged.** I(word; length) recomputed on a random half of the tokens moves by
0.000 bits. An estimate still drifting between N/2 and N is not converged whatever
its correction says, so this is reported rather than assumed.

**H(L) carries the headline, and not I or the ratio.** H(L) has ~20 values and
millions of samples. H(word) and H(word|length) both sit on a heavy tail whose mass
is in types this corpus never saw; both are underestimated by an amount no
first-order correction can see, and the conditional's bins are smaller so its unseen
mass is proportionally larger. The direction of the *ratio's* bias is genuinely
unknown.

**The Miller–Madow correction is not where the uncertainty lives, and the arm was
built believing the opposite.** It was written expecting the plug-in estimator to
*inflate* I — "biased down, and biased down harder on the conditional, because each
length bin holds fewer samples". The test asserting that direction failed on its
first run. Every word has exactly one length, so the observed types partition across
the bins: the conditional's corrections sum to (K−L)/2N against the marginal's
(K−1)/2N, and therefore

    I_plugin = I_MillerMadow − (L−1)/(2N ln2)

— the plug-in *understates* I, by ~10⁻¹⁶ bits at this N. The direction was a guess.
The identity is not. Both figures are in the artifact.

## The collision arm, and why its most quotable number is worthless

Arm 3 counts how many **distinct corpus sentences share one exact signature**. Pooled
over the window it looks like this:

| corpus fraction | distinct sentences | unique signature | group a sentence lands in |
|---:|---:|---:|---:|
| 10% | 76,127 | 91.8% | 1.4 |
| 25% | 190,318 | 88.8% | 2.0 |
| 50% | 380,636 | 86.5% | 2.9 |
| 100% | 761,273 | 83.9% | 4.8 |

**Read the first column, not the third.** "84% of signatures are unique" invites
"then the shape nearly identifies the sentence", and the subsample control is there
to kill that reading: uniqueness *falls* and group size *grows* monotonically as the
corpus grows, with no sign of settling. In-corpus uniqueness is a statement about the
corpus's size, not about English.

Per sentence length the sparsity is naked:

| n | distinct sentences | unique signature | group | shape bits ≤ | word bits (unigram) |
|---:|---:|---:|---:|---:|---:|
| 3 | 35,880 | 1.3% | 63.5 | 9.9 | 33.8 |
| 5 | 45,223 | 46.1% | 2.8 | 16.5 | 56.4 |
| 8 | 77,629 | 96.3% | 1.3 | 26.4 | 90.3 |
| 12 | 129,195 | 98.9% | 1.0 | 39.6 | 135.4 |

A 12-word shape indexes 2⁴¹ ≈ 2·10¹² possibilities and the corpus offers 1.3·10⁵
sentences to spread over them, so uniqueness at n=12 is *arithmetically forced* and
measures nothing. At n=3 there is no room to hide and 63 sentences share the average
shape. The two arms are wrong in opposite directions **on purpose**: arm 2 assumes
positions are independent and so overstates how many sentences fit a shape; arm 3
counts only what this corpus held and so understates.

The `shape bits ≤` / `word bits` ratio is constant at 29.2% down the table. That is a
tautology — both columns are per-word quantities times n — and is printed only so
nobody mistakes its constancy for a finding.

## What this changes for `stage_1/`

`stage_1/README.md` frames success as "the model reconstructs plausible, grammatical,
context-appropriate sentences" and failure as "collapses to repetitive nonsense". Both
outcomes are compatible with the channel being nearly empty, so neither is a
measurement of the model. The target is the **ceiling**: a model given only lengths
cannot do better than 3.30 bits per word, and the question worth asking is how close
to that it gets — against a model given *no* input at all, which is the same prior
control that dissolved the recovery result.

## Running it

```bash
python3 measure/ceiling.py                                  # wikitext-103, both tokenisers
python3 measure/ceiling.py --hf-config wikitext-2-raw-v1    # small and fast
python3 measure/ceiling.py --corpus-file mytext.txt         # no huggingface at all
python3 measure/test_ceiling.py                             # 11 arms, 6 mutants driven red
```

Needs `datasets` only for the huggingface path. No model, no network, no API key —
which is the point — this arm cannot be wrong about a *reader*. It can still be wrong
about the CORPUS, and it was.

**THE HEADLINE SHIPPED 0.12 BITS HIGH FOR A DAY (found by outside review, 2026-08-30).**
`arm_capacity_and_word` accepts a list or a Counter; `main()` passes only a Counter, and
`Counter(len(w) for w in words)` iterates a Counter's KEYS. So H(L) was the entropy of a
198,898-word type inventory instead of 6.89M running tokens: 3.42 reported against 3.30
true. Two independent reasons no test saw it. Every test passed a LIST, so the only live
path was never executed — and one of them names "reading H(length) off the wrong Counter"
as a mutant it would catch, which it would have, on the branch it never took. And the
assertion was `I <= H(L)`, while the truth is `I == H(L)` exactly (H(L|W)=0: every word has
one length). The bug inflated H(L), so the *bound passed because of the defect*, and that
test's own comment said a failure would mean "the two quantities were computed off
different populations" — which is precisely what had happened.

Fixed three ways rather than one: the counter is built from `wc.items()` with counts; the
assertion is the identity to 12 places; and the artifact now publishes
`identity_residual_bits` so any future population mismatch is VISIBLE in the output instead
of hidden inside a satisfied inequality. Every test now runs over both input shapes through
a `both_forms()` helper. Restoring the original bug turns three independent arms red.

The lesson generalises past this file: **a bound is not a measurement of the thing it
bounds.** The same slack hid a docstring that stated the Miller–Madow term's magnitude ten
orders of magnitude too low — the only assertion on it was that it is small, which a
decorative claim satisfies as easily as a true one.

---

# Does the ceiling hold in another language?

The 3.30 bits above is English. It is worth asking whether Silent Language is an English
trick or a property of writing, and the answer is computable with the same instrument.

Both corpora come from `wikimedia/wikipedia` (`20231101.en`, `20231101.ru`), streamed
through **one pipeline, one tokeniser** (`\b\w+\b`, which is Unicode and sees Cyrillic and
Latin alike), and **matched on token count to 0.006%** — 6,885,217 against 6,885,609.
`measure/extract_corpus.py` does the streaming and stops on a budget counted in tokens
*inside* the 3–12-word window, so the number budgeted is the number the estimator sees.

| | English | Russian |
|---|---:|---:|
| mean word length | 4.93 | 6.12 |
| word types (case folded) | 267,592 | 474,623 |
| **H(length) = I(word;length)** | **3.345** | **3.701** |
| H(word) | 11.821 | 14.064 |
| **H(word \| length)** — what the receiver supplies | **8.476** | **10.364** |
| share the shape carries | 28.3% | 26.3% |
| **equiprobable words per slot** | **356** | **1,318** |

The receiver's slot is **3.7× wider in Russian**. A ten-word sentence leaves an English
receiver ~85 bits to supply and a Russian one ~104.

**That number is a size, not a verdict.** It is the size of the admissible set, and which
word you use for it depends on what you want. If you want to RECOVER the original it is
difficulty. If you want to INVENT — which is what this project says reading is — it is
room: the same skeleton supports 3.7× more different coherent readings. By the repository's
own stated values the Russian channel is not worse, it is richer. Both readings of the same
number are correct and the table names neither as the true one.

Two predictions were written down before the run and both held: Russian has higher
H(length) (longer, more varied words; no articles piling up short tokens) and much higher
H(word) (1.8× the vocabulary at equal N). The share was left genuinely open, and it came
out *lower* — morphology inflates the vocabulary faster than it inflates length variety.

## The control that makes this comparable

English was **re-measured through this pipeline** even though wikitext-103 had already
answered. It gives 3.345 here against 3.305 there. So corpus processing moves the number by
0.04 bits and language moves it by 0.36 — the language effect is ~9× the pipeline artifact.
Run on two differently-prepared corpora, those two would not be separable, and the
difference would have been reported as language.

## Three things this does not establish

- **The share difference is the weakest number in the table**, at 1.7 percentage points.
  Russian carries 1.77× the types at equal N, so its heavier tail is less well sampled and
  *both* its entropies are underestimated by more. Which way that pushes a RATIO is not
  settled here. The robust claims are H(length) — small support, tightly estimated — and the
  1.82-bit absolute gap in H(word|length).
- **The collision arm is not reported per language**, though the figure is tempting (a
  Russian sentence lands in a group of 19.3 against 6.6). At equal tokens Russian yielded
  more in-window sentences (868,465 vs 779,268), i.e. they are shorter in WORDS — 7.93
  against 8.84. Fewer positions, smaller shape space, more collisions, mechanically. That is
  a sentence-length difference wearing a language label, and it needs a length-controlled
  comparison before it means anything.
- **Morphology and word order cannot be separated.** The estimator is unigram; word order is
  invisible to it. Russian's freer order constrains the next word less, which pushes the same
  direction as the larger vocabulary and is folded into the same 1.82 bits. The difference is
  nameable; its causes are not decomposable by this instrument.

Artifacts: [`result-ceiling-en-wikipedia.json`](result-ceiling-en-wikipedia.json),
[`result-ceiling-ru-wikipedia.json`](result-ceiling-ru-wikipedia.json).

---

# One ruler, several constraints

Silent Language is not a subject, it is a point in a space. `measure/constraints.py` puts
the Oulipo forms beside it in ONE unit — bits per word, same corpus, same unigram model —
with three columns kept deliberately apart:

- **writer pays** — expressive freedom the constraint removes
- **channel carries** — what the transmitted skeleton says *about this message*
- **receiver supplies** — what is left to invent, given everything sent

English (wikipedia, 6.89M tokens, case folded):

| constraint | writer pays | channel carries | receiver supplies |
|---|---:|---:|---:|
| silent-language | 3.345 | **3.345** | 8.448 |
| pilish | 3.345 | 0.000 | 8.448 |
| snowball | 3.345 | 0.000 | 8.448 |
| lipogram, no *e* | 1.522 | 0.000 | 10.271 |
| lipogram, no *t* | 0.608 | 0.000 | 11.186 |
| univocalic in *a* | 3.601 | 0.000 | 8.192 |
| N+7 | 0.000 | 0.000 | 11.793 |

Russian (same pipeline, script-appropriate predicates):

| constraint | writer pays | channel carries | receiver supplies |
|---|---:|---:|---:|
| silent-language | 3.701 | **3.701** | 10.314 |
| pilish / snowball | 3.701 | 0.000 | 10.314 |
| lipogram, no *о* | 1.687 | 0.000 | 12.327 |
| lipogram, no *т* | 1.038 | 0.000 | 12.977 |
| univocalic in *а* | 4.970 | 0.000 | 9.044 |
| N+7 | 0.000 | 0.000 | 14.015 |

**The inversion, numerically.** Pilish and Snowball constrain word lengths exactly as
Silent Language does and their writers pay exactly the same price. Their skeleton is π's
digits, or 1,2,3,4… — a *public constant*, known before the text exists — so it carries
nothing about this message. Same sacrifice; one buys a channel, the other buys only the
discipline. Silent Language transmits **only** the skeleton; the Oulipo forms transmit
everything else and never the skeleton.

**The trade nobody had written down.** The harder the writer is constrained, the *less*
the receiver must supply. Univocalism costs the writer most (3.601) and leaves the
receiver least (8.192); N+7 costs nothing — a bijection removes no freedom — and leaves
the receiver everything (11.793). Constraint and recoverability are one trade, and Silent
Language sits in its strange corner: the vocabulary is barely constrained (any word of the
right length will do) while the receiver is maximally adrift.

## A predicate in the wrong alphabet does not fail, it admits everything

The Russian rows were nonsense on the first run: a univocalism came out costing 0.12 bits
and leaving 13.89 — admitting essentially the whole vocabulary — because the predicates
tested for the *Latin* letters `e`, `t` and the Latin vowel set, which barely occur in
Cyrillic. The constraint did not error. It quietly held for almost every word.

This is the same failure as a Latin tokeniser over Cyrillic, which `ceiling.py` was taught
to refuse earlier the same day, reintroduced two files later because the predicates were
written as literals. So: the script is **detected from token mass**, the vowel set and
lipogram targets come from it, and any constraint admitting more than 98% of tokens is
reported `INAPPLICABLE` with its share — never as a cheap constraint. A near-zero cost is
far more likely to mean the wrong alphabet than an easy rule.

Artifacts: [`result-constraints-en.json`](result-constraints-en.json),
[`result-constraints-ru.json`](result-constraints-ru.json).
