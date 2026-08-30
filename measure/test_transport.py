#!/usr/bin/env python3
"""Tests for measure/transport.py and the plural notation in silent.py.

Driven red by mutation before being trusted; each test names its mutant.
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import silent      # noqa: E402
import transport   # noqa: E402


class TestForms(unittest.TestCase):
    def test_the_shipped_notation_round_trips(self):
        s = "The night is long and the city keeps its silence"
        self.assertEqual(silent.lengths(silent.encode(s)), [len(w) for w in s.split()])

    def test_every_candidate_round_trips_the_same_lengths(self):
        """The candidates are ONE channel written six ways. If any of them disagrees
        about the lengths, the comparison between them is meaningless.

        RED under: any candidate encode/decode pair drifting out of step.
        """
        s = "The night is long and the city keeps its silence"
        want = [len(w) for w in s.split()]
        for form in transport.CANDIDATES:
            with self.subTest(form=form):
                self.assertEqual(transport._lengths(form, transport._encode(form, s)), want)

    def test_the_measurement_takes_the_shipped_mark_from_silent_not_a_copy(self):
        """`block` must BE what silent.py ships. A second copy of the mark here would
        drift the day the mark changes, and this file's whole job is to be the reason
        that mark is what it is.

        RED under: CANDIDATES['block'] carrying its own literal.
        """
        self.assertIn(silent.MARK, transport._encode("block", "night"))
        self.assertEqual(transport._encode("block", "night"), silent.encode("night"))

    def test_brackets_cannot_be_parsed_by_splitting(self):
        """The bracket run's own content IS spaces, so whitespace splitting cuts every
        run to pieces. Scanning is not an implementation taste here.

        RED under: _lengths() using encoded.split() for the bracket candidate.
        """
        enc = transport._encode("brackets", "The night is long")
        self.assertNotEqual([len(c) for c in enc.split()], [3, 5, 2, 4])
        self.assertEqual(transport._lengths("brackets", enc), [3, 5, 2, 4])

    def test_the_shipped_mark_is_not_markdown_syntax(self):
        """The one property the shipped notation was chosen FOR. An ASCII underscore
        line is a horizontal rule and the message does not arrive at all.

        RED under: MARK = '_' (or '*', or '-').
        """
        self.assertNotIn(silent.MARK, "_*-=#>`~[]()!|")


class TestClassify(unittest.TestCase):
    """The three outcomes must be three, and the middle one is why this file exists."""

    def test_intact(self):
        v, got = transport.classify("dots", [3, 5], "··· ·····")
        self.assertEqual((v, got), ("intact", [3, 5]))

    def test_a_well_formed_wrong_answer_is_silent_not_loud(self):
        """A collapsed '( )' parses perfectly and means something else. Calling that
        'corrupted' without the word SILENTLY loses the only fact that matters.

        RED under: classify() returning 'corrupted-loudly' for a parse that succeeded.
        """
        v, got = transport.classify("brackets", [3, 5, 2, 4], "( ) ( ) ( ) ( )")
        self.assertEqual(v, "corrupted-silently")
        self.assertEqual(got, [1, 1, 1, 1])

    def test_unparseable_is_loud(self):
        v, got = transport.classify("brackets", [3, 5], "(   ) oops (     )")
        self.assertEqual(v, "corrupted-loudly")

    def test_absent_medium_is_na_never_a_pass(self):
        """A missing browser must not read as 'it survived'. The failure direction of a
        silently-skipped medium is a false all-clear.

        RED under: classify() returning 'intact' when received is None.
        """
        v, got = transport.classify("dots", [3, 5], None)
        self.assertEqual(v, "na")


if __name__ == "__main__":
    unittest.main(verbosity=2)
