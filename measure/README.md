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
readings can agree with each other while all being wrong. So each arm-A reading
is compared to the *true* original and to **decoys carrying the same length
profile**. A reading no closer to the truth than to a matched decoy has
recovered nothing, however convergent the arm is.

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

## Running it

```bash
python3 measure/silent_channel.py --text "your known message" -n 20
```

Needs a reader command taking a prompt as `argv[1]` and printing the reply
(`--relay`, default `mesh-relay`), and any embedding endpoint for the semantic
metric (`--no-embed` to skip). Every reading, arm and pair lands in the JSON
artifact so the numbers can be recomputed without re-running the models.
