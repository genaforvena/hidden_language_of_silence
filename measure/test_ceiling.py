#!/usr/bin/env python3
"""Tests for measure/ceiling.py.

Every arm here has been driven RED by mutating ceiling.py and watching it fail;
a gate nobody has seen fail is not a gate. The mutants are named in each test.
"""
import hashlib, math, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import ceiling  # noqa: E402
from collections import Counter  # noqa: E402


def both_forms(words):
    """EVERY arm runs on BOTH input shapes.

    This helper is the whole lesson of the 2026-08-30 review. `arm_capacity_and_word`
    accepts a list or a Counter, main() passes ONLY a Counter, and every test passed only
    a list -- so the sole live path was never exercised once. The bug it hid was
    `Counter(len(w) for w in words)`, which iterates a Counter's KEYS: H(L) was the
    entropy of a 198,898-word type inventory instead of 6.89M running tokens, and the
    headline shipped 0.12 bits too high into the README, SPEC.md and two other files.
    A branch no test takes is not covered by the tests that take the other branch.
    """
    return [("list", list(words)), ("counter", Counter(words))]


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

    def test_mutual_information_EQUALS_the_channel_capacity(self):
        """I(W;L) == H(L) EXACTLY, because H(L|W)=0: every word has one length.

        This assertion used to be `assertLessEqual`, and the inequality PASSED BECAUSE OF
        the type-vs-token bug -- the defect inflated H(L), so a loose bound was satisfied
        by the very thing it should have caught. Its own comment said a failure would mean
        "the two quantities were computed off different populations". That is exactly what
        had happened, and the assertion was too weak to say so.

        RED under: building the length counter off the Counter's keys (the shipped bug).
        """
        words = ["a", "bb", "bc", "ccc", "ccd", "cce", "dddd"] * 7 + ["zz"] * 3
        for name, form in both_forms(words):
            with self.subTest(form=name):
                r = ceiling.arm_capacity_and_word(form)
                self.assertAlmostEqual(r["I_word_length_bits"]["plugin"],
                                       r["H_length_bits"]["plugin"], places=12)
                self.assertAlmostEqual(r["identity_residual_bits"]["plugin"], 0.0, places=12)

    def test_the_length_distribution_counts_TOKENS_not_types(self):
        """The artifact's own tell. length_distribution must sum to the token count; when
        it summed to the TYPE count that was the bug, printed in the file, unread.

        RED under: the shipped bug, directly.
        """
        words = ["aa"] * 500 + ["bb"] * 3 + ["ccc"]
        for name, form in both_forms(words):
            with self.subTest(form=name):
                r = ceiling.arm_capacity_and_word(form)
                self.assertEqual(sum(r["length_distribution"].values()), r["tokens"])
                self.assertEqual(r["length_distribution"][2], 503)

    def test_both_input_forms_agree_on_every_published_number(self):
        """A list and a Counter of the same corpus ARE the same corpus.

        RED under: any per-branch divergence, which is the class the review found.
        """
        words = ["a", "bb", "bb", "ccc", "ccc", "ccc", "dddd"] * 5
        (_, as_list), (_, as_ctr) = both_forms(words)
        a = ceiling.arm_capacity_and_word(as_list)
        b = ceiling.arm_capacity_and_word(as_ctr)
        for k in ("H_word_bits", "H_length_bits", "H_word_given_length_bits",
                  "I_word_length_bits"):
            self.assertAlmostEqual(a[k]["plugin"], b[k]["plugin"], places=12, msg=k)
        self.assertEqual(a["length_distribution"], b["length_distribution"])
        self.assertEqual(a["tokens"], b["tokens"])


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

    def test_the_stated_size_of_the_correction_is_the_measured_one(self):
        """The docstring must quote the term's ACTUAL magnitude at this corpus's own
        N and L, not a number nobody checked.

        An earlier draft said "around 1e-16 bits". The real value at N=6.89e6, L=32 is
        3.2e-6 -- wrong by ten orders of magnitude, and invisible because the only
        assertion was `< 1e-6`, which a decorative claim satisfies as easily as a true
        one. A bound is not a measurement of the thing it bounds.

        RED under: restoring any 1e-1x claim, or drifting the corpus figures.
        """
        n, n_lengths = 6.89e6, 32
        term = (n_lengths - 1) / (2 * n * math.log(2))
        self.assertAlmostEqual(term, 3.2e-6, delta=0.1e-6)
        src = open(os.path.join(HERE, "ceiling.py"), encoding="utf-8").read()
        self.assertIn("3.2e-6 bits", src)
        self.assertNotIn("1e-16", src)

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
