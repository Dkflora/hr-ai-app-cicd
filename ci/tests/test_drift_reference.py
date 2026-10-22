"""The Evidently drift reference must belong to the current test cases.

ci/prepare_drift.py refuses to compare a run with a reference built from different cases.
Without this test, changing evaluation_questions.json would only fail later, in the
candidate job on main. Here it fails in the checks job, on the pull request.
"""
import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class DriftReferenceTests(unittest.TestCase):

    def test_reference_matches_the_current_test_cases(self):
        cases = json.loads((ROOT / 'lambda/data/evaluation_questions.json').read_text(encoding='utf-8'))
        canonical = json.dumps(cases, sort_keys=True, separators=(',', ':')).encode()
        reference = json.loads((ROOT / 'ci/data/drift-reference.json').read_text())
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), reference['case_definitions_sha256'],
                         'The test cases changed: rebuild ci/data/drift-reference.* from a passing run')

    def test_reference_has_enough_rows(self):
        with (ROOT / 'ci/data/drift-reference.csv').open(encoding='utf-8') as file:
            rows = list(csv.DictReader(file))
        self.assertGreaterEqual(len(rows), 10)   # prepare_drift.py needs at least ten
        self.assertEqual(set(rows[0]), {'answer_length', 'latency_seconds'})


if __name__ == '__main__':
    unittest.main()
