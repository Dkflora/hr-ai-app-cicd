"""Tests for the number comparison in ci/quality_checks.py, and how the report shows it.

Embeddings scored "carry over 5 days" and "carry over 20 days" at 0.896, above the 0.75 pass
mark, so two answers that contradict each other could look consistent. The number comparison
catches that, and the report asks a person to look. It never fails the gate.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quality_checks import numbers_differ, numbers_in
from report import quality_section


class NumberComparisonTests(unittest.TestCase):

    def test_contradicting_numbers_are_flagged(self):
        self.assertTrue(numbers_differ('You can carry over up to 5 days.', 'You can carry over up to 20 days.'))

    def test_the_same_numbers_in_other_words_are_not_flagged(self):
        self.assertFalse(numbers_differ('You can carry over up to 5 days.', 'Up to 5 unused days roll over.'))

    def test_commas_do_not_matter(self):
        self.assertEqual(numbers_in('The band is 152,000 to 192,000.'), {'152000', '192000'})


class ReportTests(unittest.TestCase):

    def quality(self, numbers_differ_cases):
        return {'latency_seconds': {'answers': 0, 'limit': 20.0},
                'retrieval': {'cases': 1, 'misses': [], 'mean_reciprocal_rank': 1.0},
                'consistency': {'lowest': 0.9, 'threshold': 0.75, 'failures': [],
                                'numbers_differ': numbers_differ_cases}}

    def test_flagged_pairs_are_named_by_case_number_only(self):
        text, passed = quality_section(self.quality(['6']), None)
        self.assertIn('different numbers in case 7', text)
        self.assertTrue(passed)   # report only: the gate still passes

    def test_nothing_is_said_when_numbers_agree(self):
        text, _ = quality_section(self.quality([]), None)
        self.assertNotIn('Check by hand', text)


if __name__ == '__main__':
    unittest.main()
