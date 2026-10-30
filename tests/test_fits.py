"""Unit tests for statistical analysis functions in fits.py.

Zero API calls. Tests mathematical properties of AUC, paired DeLong,
clustered bootstrap, and Brier Skill Score against known hand-calculated fixtures.
Governed by PRD §4, §8, §10.
"""

import unittest
import numpy as np

from ofrenda import fits


class FitsTest(unittest.TestCase):
    def test_auc_perfect(self):
        y_true = np.array([1, 1, 0, 0])
        y_score = np.array([0.9, 0.8, 0.2, 0.1])
        self.assertAlmostEqual(fits.compute_auc(y_true, y_score), 1.0)

    def test_auc_reversed(self):
        y_true = np.array([1, 1, 0, 0])
        y_score = np.array([0.1, 0.2, 0.8, 0.9])
        self.assertAlmostEqual(fits.compute_auc(y_true, y_score), 0.0)

    def test_paired_delong_identical_scores(self):
        y_true = np.array([1, 1, 0, 0, 1, 0])
        y_score = np.array([0.8, 0.7, 0.3, 0.2, 0.9, 0.1])
        res = fits.paired_delong_auc_diff(y_true, y_score, y_score)
        self.assertEqual(res["diff"], 0.0)
        self.assertEqual(res["se_diff"], 0.0)
        self.assertTrue(res["non_inferior"])

    def test_paired_delong_non_inferiority(self):
        # A is slightly better or equal to B
        y_true = np.array([1, 1, 1, 0, 0, 0] * 5)
        score_a = np.array([0.9, 0.85, 0.8, 0.2, 0.15, 0.1] * 5)
        score_b = np.array([0.88, 0.82, 0.79, 0.25, 0.18, 0.12] * 5)
        res = fits.paired_delong_auc_diff(y_true, score_a, score_b)
        self.assertGreaterEqual(res["auc_a"], res["auc_b"])
        self.assertTrue(res["non_inferior"])
        self.assertLess(res["ci_upper_one_sided"], 0.07)

    def test_brier_score_and_skill(self):
        # Perfect predictions: Brier=0, BSS=1
        y_true = np.array([1, 0])
        y_prob = np.array([1.0, 0.0])
        res = fits.brier_score_and_skill(y_true, y_prob)
        self.assertEqual(res["brier"], 0.0)
        self.assertEqual(res["bss"], 1.0)

        # Base rate predictions: BSS=0
        y_true = np.array([1, 1, 0, 0])
        y_prob = np.array([0.5, 0.5, 0.5, 0.5])
        res = fits.brier_score_and_skill(y_true, y_prob)
        self.assertEqual(res["bss"], 0.0)

    def test_monotonicity_check(self):
        p1 = np.array([0.8, 0.6, 0.4])
        p2 = np.array([0.7, 0.6, 0.3])
        res = fits.monotonicity_check(p1, p2)
        self.assertEqual(res["violations"], 0)
        self.assertEqual(res["violation_rate"], 0.0)

        p2_bad = np.array([0.9, 0.6, 0.3])  # 0.9 > 0.8
        res_bad = fits.monotonicity_check(p1, p2_bad)
        self.assertEqual(res_bad["violations"], 1)
        self.assertAlmostEqual(res_bad["violation_rate"], 1.0 / 3.0, places=4)

    def test_repo_clustered_bootstrap(self):
        rows = []
        for r in range(10):
            for t in range(3):
                y = 1 if (r % 2 == 0) else 0
                rows.append({
                    "repo": f"repo_{r}",
                    "y1": y,
                    "pred_a": 0.8 if y == 1 else 0.2,
                    "pred_b": 0.75 if y == 1 else 0.25,
                })
        res = fits.repo_clustered_bootstrap(
            rows, score_a_col="pred_a", score_b_col="pred_b", target_col="y1", n_resamples=50
        )
        self.assertIn("ci_upper_one_sided", res)
        self.assertTrue(res["non_inferior"])


if __name__ == "__main__":
    unittest.main()
