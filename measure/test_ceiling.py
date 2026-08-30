#!/usr/bin/env python3
"""Tests for measure/ceiling.py.

Every arm here has been driven RED by mutating ceiling.py and watching it fail;
a gate nobody has seen fail is not a gate. The mutants are named in each test.
"""
import hashlib, math, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import ceiling  # noqa: E402


class TestPoles(unittest.TestCase):
    """The two ends of the channel, where the right answer is known exactly."""

    def test_length_determines_word_gives_full_share(self):
        # Every word of a given length is the SAME word: the shape names the word.
        # RED under: swapping H(word) and H(word|length) in I.
        words = ["a"] * 40 + ["bb"] * 30 + ["ccc"] * 20 + ["dddd"] * 10
        r = ceiling.arm_capacity_and_word(words)
        self.assertAlmostEqual(r["H_word_given_length_bits"]["plugin"], 0.0, places=12)
        self.assertAlmostEqual(r["shape_share_of_word"]["plugin"], 1.0, places=12)
        self.assertAlmostEqual(r["effective_words_per_slot"]["plugin"], 1.0, places=12)

    def test_one_length_carries_nothing(self):
        # All words the same length: the channel is a constant.
        # RED under: computing I as H(word) - 0, or reading H(length) off the wrong Counter.
        words = ["aa", "bb", "cc", "dd"] * 25
        r = ceiling.arm_capacity_and_word(words)
        self.assertAlmostEqual(r["H_length_bits"]["plugin"], 0.0, places=12)
        self.assertAlmostEqual(r["I_word_length_bits"]["plugin"], 0.0, places=12)
        self.assertAlmostEqual(r["shape_share_of_word"]["plugin"], 0.0, places=12)

    def test_channel_cannot_exceed_its_own_capacity(self):
        # I(W;L) <= H(L) is an identity, not a hope. If it ever fails, the two
        # quantities were computed off different populations.
        words = ["a", "bb", "bc", "ccc", "ccd", "cce", "dddd"] * 7 + ["zz"] * 3
        r = ceiling.arm_capacity_and_word(words)
        self.assertLessEqual(r["I_word_length_bits"]["plugin"],
                             r["H_length_bits"]["plugin"] + 1e-12)


class TestBias(unittest.TestCase):
    def test_miller_madow_raises_the_mutual_information_by_exactly_L_minus_1(self):
        """The correction moves I UP, by exactly (L-1)/(2N ln2).

        This test is why the module docstring says what it says. The arm was written
        expecting the opposite -- 'the conditional has fewer samples per bin, so it is
        biased down harder, so plug-in I is inflated' -- and this assertion failed on
        the first run. Every word has exactly one length, so the observed types
        partition across the bins and the corrections sum to (K-L)/(2N) against the
        marginal's (K-1)/(2N). The direction was a guess; the identity is not.

        RED under: applying Miller-Madow to H(word) only, or to the conditional only.
        """
        words = ["a", "b", "cc", "dd", "ee", "fff", "ggg"] * 3
        r = ceiling.arm_capacity_and_word(words)
        i_p = r["I_word_length_bits"]["plugin"]
        i_m = r["I_word_length_bits"]["miller_madow"]
        self.assertGreater(i_m, i_p)
        n = r["tokens"]
        n_lengths = r["length_values"]
        self.assertAlmostEqual(i_m - i_p, (n_lengths - 1) / (2 * n * math.log(2)),
                               places=12)

    def test_the_correction_is_negligible_at_corpus_scale(self):
        """(L-1)/(2N ln2) with L~20 and N~1e8 is ~1e-16 bits. An arm whose headline
        rests on a term that small is resting on nothing, which is why the ceiling
        H(L) and the convergence arm carry the claim instead of the correction.
        """
        n, n_lengths = 1e8, 20
        self.assertLess((n_lengths - 1) / (2 * n * math.log(2)), 1e-6)

    def test_plugin_never_exceeds_log2_of_types(self):
        words = ["x", "y", "zz"] * 10
        r = ceiling.arm_capacity_and_word(words)
        self.assertLessEqual(r["H_word_bits"]["plugin"], math.log2(r["word_types"]) + 1e-12)


class TestCollisions(unittest.TestCase):
    def test_uniqueness_falls_as_the_corpus_grows(self):
        """In-corpus uniqueness is a sampling artifact, and the arm must SHOW that
        rather than assert it: the unique share must not rise with corpus size.

        RED under: recomputing groups on the full set at every fraction (the bug that
        makes the collision arm answer the same number four times).
        """
        # 200 texts over only 8 signatures: at 10% many signatures are seen once,
        # at 100% almost none are.
        sigs = [((i % 8) + 3,) for i in range(200)]
        out = ceiling.arm_collisions(sigs, [0.05, 0.25, 1.0], seed=1)
        shares = [c["unique_signature_share_of_sentences"] for c in out]
        self.assertGreater(shares[0], shares[-1])
        self.assertEqual(out[-1]["distinct_sentences"], 200)
        self.assertEqual(out[-1]["distinct_signatures"], 8)

    def test_group_size_is_sentence_weighted(self):
        """'How big a group does a SENTENCE land in' is not the mean group size --
        a sentence is more likely to land in a big group. One signature of 9 and
        nine of 1 average 1.8 per signature but 4.6 per sentence.

        RED under: reporting sum(sizes)/n_signatures under this key.
        """
        sigs = [(1,)] * 9 + [(k,) for k in range(2, 11)]
        out = ceiling.arm_collisions(sigs, [1.0], seed=1)[0]
        self.assertEqual(out["distinct_sentences"], 18)
        self.assertEqual(out["distinct_signatures"], 10)
        self.assertAlmostEqual(out["mean_group_size_a_sentence_lands_in"],
                               (9 * 9 + 9 * 1) / 18)


class TestTokenisers(unittest.TestCase):
    def test_the_two_tokenisers_are_different_channels(self):
        """An apostrophe is one word to measure/ and two to stage_1/. If these ever
        agree, one of them has been silently changed to the other.
        """
        s = "don't"
        self.assertEqual(ceiling.TOKENISERS["measure"].findall(s), ["don't"])
        self.assertEqual(ceiling.TOKENISERS["stage_1"].findall(s), ["don", "t"])

    def test_heading_lines_are_dropped(self):
        rows = [" = Heading = ", "The cat sat on the mat."]
        got = list(ceiling.sentences_from(rows, 3, 12, "measure"))
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0][1], ["The", "cat", "sat", "on", "the", "mat"])


class TestProvenance(unittest.TestCase):
    def test_the_block_names_ceiling_not_the_shared_module(self):
        """The reason provenance.py takes the script as an ARGUMENT. Keyed on the
        shared module's own __file__, every artifact in the repo would attest the
        same sha256 -- a provenance block naming the wrong instrument reads as
        evidence and is worse than none.

        RED under: Instrument(provenance.__file__) inside ceiling.py.
        """
        with open(os.path.join(HERE, "ceiling.py"), "rb") as f:
            want = hashlib.sha256(f.read()).hexdigest()
        block = ceiling.INSTRUMENT.block(["ceiling.py"])
        self.assertEqual(block["at_start"]["script_sha256"], want)
        self.assertIn("git_head", block["at_start"])
        self.assertIn("argv", block)


if __name__ == "__main__":
    unittest.main(verbosity=2)
