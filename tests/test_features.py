"""Feature-arithmetic tests over synthetic fixtures. Zero API calls.

Fixtures come from test_labels (one definition). Each test pins a registered
feature to a hand-computed value so the arithmetic cannot drift silently.
"""

import datetime as dt
import json
import math
import tempfile
import unittest
from pathlib import Path

from ofrenda import features
try:
    from test_labels import (T, commit, comment, corridor, issue, release, repo)
except ImportError:  # direct `unittest tests.test_features` runs
    from tests.test_labels import (
        T, commit, comment, corridor, issue, release, repo,
    )


class F1Test(unittest.TestCase):
    def test_ratio_and_companion(self):
        source = repo(releases=[
            release(T(2014, 12, 1), login="keeper"),   # outside both windows
            release(T(2015, 2, 1), login="keeper"),    # prior: gap 30d
            release(T(2015, 3, 3), login="keeper"),
            release(T(2018, 2, 1), login="keeper"),    # recent: gap 120d
            release(T(2018, 6, 1), login="keeper"),
        ])
        value, never = features.f1_release_decay(source, T(2019, 1, 1))
        self.assertAlmostEqual(value, 4.0, places=6)
        self.assertFalse(never)

    def test_single_release_in_a_window_is_none(self):
        source = repo(releases=[
            release(T(2015, 2, 1), login="keeper"),    # prior: 1 stamp, no gap
            release(T(2017, 6, 1), login="keeper"),    # recent: 1 stamp
        ])
        value, never = features.f1_release_decay(source, T(2019, 1, 1))
        self.assertIsNone(value)
        self.assertFalse(never)

    def test_never_released(self):
        value, never = features.f1_release_decay(repo(), T(2019, 1, 1))
        self.assertIsNone(value)
        self.assertTrue(never)


class F2Test(unittest.TestCase):
    def test_entropy_value(self):
        source = repo(commits=[
            commit(T(2018, 3, 3), login="dev"),   # gap 1d   -> bin 1
            commit(T(2018, 3, 4), login="dev"),
            commit(T(2018, 3, 6), login="dev"),   # gap 2d   -> bin 1
            commit(T(2018, 6, 20), login="dev"),  # gap 106d -> bin 4
            commit(T(2018, 6, 21), login="dev"),  # gap 1d   -> bin 1
            commit(T(2017, 6, 1), login="dev"),   # outside [T-12mo, T)
        ])
        value = features.f2_commit_entropy(source, T(2019, 1, 1))
        self.assertAlmostEqual(value, 0.811278, places=5)

    def test_single_bin_is_zero(self):
        stamps = [T(2018, m, 1) for m in range(1, 13)]   # ~monthly gaps: bin 1 (28-31d)
        source = repo(commits=[commit(t, login="dev") for t in stamps])
        self.assertEqual(features.f2_commit_entropy(source, T(2019, 1, 1)), 0.0)

    def test_degenerate_cases(self):
        self.assertIsNone(features.f2_commit_entropy(repo(), T(2019, 1, 1)))
        one = repo(commits=[commit(T(2018, 6, 1), login="dev")])
        self.assertIsNone(features.f2_commit_entropy(one, T(2019, 1, 1)))
        # bot commits do not supply intervals
        bots = repo(commits=[commit(T(2018, 3, 3), login="x[bot]"),
                             commit(T(2018, 3, 6), login="y[bot]")])
        self.assertIsNone(features.f2_commit_entropy(bots, T(2019, 1, 1)))

    def test_bin_edges(self):
        # gaps of exactly 3d and 14d land in the 1-3 and 14-45 bins
        source = repo(commits=[
            commit(T(2018, 1, 1), login="dev"),
            commit(T(2018, 1, 4), login="dev"),    # 3d
            commit(T(2018, 1, 18), login="dev"),   # 14d
        ])
        value = features.f2_commit_entropy(source, T(2018, 7, 1))
        self.assertAlmostEqual(value, 1.0, places=6)   # two occupied bins, 50/50


class F4F5Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = repo(issues=[
            issue(1, T(2018, 2, 1), "s1"),      # recent, answered 2018-02-05
            issue(2, T(2018, 3, 1), "s1"),      # recent, answered 2018-04-01
            issue(3, T(2017, 2, 1), "s2"),      # prior,  answered 2017-02-20
            issue(4, T(2017, 6, 1), "s2"),      # prior,  answered AFTER prior end
            issue(5, T(2018, 9, 1), "s3"),      # recent, answered AFTER T
            issue(6, T(2018, 4, 1), "someone6"),              # opener not a bot
            issue(7, T(2018, 5, 1), "s4", pr=True),   # a pull request
        ], comments=[
            comment(1, T(2018, 2, 5), "keeper", assoc="OWNER"),
            comment(2, T(2018, 4, 1), "keeper", assoc="OWNER"),
            comment(3, T(2017, 2, 20), "keeper", assoc="OWNER"),
            comment(4, T(2018, 7, 15), "keeper", assoc="OWNER"),  # post-window
            comment(5, T(2019, 3, 1), "keeper", assoc="OWNER"),   # after T
            comment(6, T(2018, 4, 2), "keeper", assoc="OWNER"),   # bot issue
            comment(7, T(2018, 5, 2), "keeper", assoc="OWNER"),   # PR issue
        ])

    def test_f4_median_latency_ratio(self):
        value, _ = features.f4_f5(self.source, T(2019, 1, 1))
        # recent latencies [1, 4, 31] -> median 4; prior [19] -> 19
        self.assertAlmostEqual(value, 4.0 / 19.0, places=6)

    def test_f5_share_difference(self):
        _, value = features.f4_f5(self.source, T(2019, 1, 1))
        # recent: opened {1,2,5,6} served {1,2,6} -> 3/4; prior: opened {3,4} served {3} -> 1/2
        self.assertAlmostEqual(value, 0.5 - 0.75, places=6)

    def test_bot_opener_is_not_a_stranger(self):
        source = repo(issues=[issue(6, T(2018, 4, 1), "dependabot[bot]")],
                      comments=[comment(6, T(2018, 4, 2), "keeper", assoc="OWNER")])
        f4, f5 = features.f4_f5(source, T(2019, 1, 1))
        self.assertIsNone(f4)
        self.assertIsNone(f5)


class F6Test(unittest.TestCase):
    def test_ratio_and_counts(self):
        source = repo(comments=(
            [comment(1, T(2018, m, 15), "keeper", assoc="OWNER") for m in (2, 9)] +
            [comment(2, T(2017, m, 15), "keeper", assoc="OWNER") for m in range(1, 6)]
        ))
        value, recent, prior = features.f6_maint_volume(source, T(2019, 1, 1))
        self.assertAlmostEqual(value, 0.4)
        self.assertEqual((recent, prior), (2, 5))

    def test_zero_prior_is_none(self):
        source = repo(comments=[comment(1, T(2018, 6, 15), "keeper", assoc="OWNER")])
        value, recent, prior = features.f6_maint_volume(source, T(2019, 1, 1))
        self.assertIsNone(value)
        self.assertEqual((recent, prior), (1, 0))


class F3Test(unittest.TestCase):
    def test_backlog_slope(self):
        source = repo(issues=[
            issue(1, T(2018, 1, 15), "s1"),                        # open through T
            issue(2, T(2018, 4, 1), "s1", closed_at=T(2018, 5, 15)),
            issue(3, T(2016, 3, 1), "s2"),                         # open through T
        ])
        # backlog by month-end (x=0..11): [2,2,3,3,2,2,2,2,2,2,2,2] -> slope -6/143
        value = features.f3_backlog_slope(source, T(2019, 1, 1))
        self.assertAlmostEqual(value, -6.0 / 143.0, places=6)

    def test_no_strangers_is_none(self):
        self.assertIsNone(features.f3_backlog_slope(repo(), T(2019, 1, 1)))


class Bf50Test(unittest.TestCase):
    def test_top_author_reaches_half(self):
        source = repo(commits=[
            commit(T(2018, 2, 1), login="a"), commit(T(2018, 3, 1), login="a"),
            commit(T(2018, 4, 1), login="a"),
            commit(T(2018, 5, 1), login="b"), commit(T(2018, 6, 1), login="b"),
            commit(T(2018, 7, 1), login="c"),
            commit(T(2017, 6, 15), login="d"),                    # outside window
            commit(T(2017, 6, 1), login="e"),                     # outside window
            commit(T(2018, 9, 1), login="dependabot[bot]"),       # bot
            commit(T(2018, 10, 1), name="less"),                  # login-less
        ])
        self.assertEqual(features.bf50(source, T(2019, 1, 1)), 1)

    def test_two_equal_authors(self):
        source = repo(commits=[commit(T(2018, 2, 1), login="a"),
                               commit(T(2018, 3, 1), login="b")])
        self.assertEqual(features.bf50(source, T(2019, 1, 1)), 1)

    def test_no_attributable_commits_is_none(self):
        source = repo(commits=[commit(T(2018, 2, 1), name="less")])
        self.assertIsNone(features.bf50(source, T(2019, 1, 1)))


class BackgroundTest(unittest.TestCase):
    def test_fields(self):
        source = repo(created=T(2012, 6, 1))
        fields = features.background(source, T(2019, 1, 1))
        self.assertAlmostEqual(fields["log10_stars"], math.log10(43), places=4)
        self.assertAlmostEqual(fields["age_years"], (T(2019, 1, 1) - T(2012, 6, 1)).total_seconds() / (86400 * 365.25), places=3)
        self.assertEqual(fields["language_py"], 1)
        self.assertEqual(fields["language_js"], 0)
        self.assertEqual(fields["created_year"], 2012)


class FeatureRowTest(unittest.TestCase):
    def test_corridor_at_2020_is_ghosting_shaped(self):
        """Social death 2018, code echoes to 2021: f2 sees the echo, f6 is dead."""
        source = corridor()
        row = features.feature_row(source, T(2020, 1, 1))
        # f6: zero maintainer comments in both windows
        self.assertEqual(row["f6_maint_volume"], None)
        self.assertEqual((row["f6_recent_comments"], row["f6_prior_comments"]), (0, 0))
        # human commits every 45d in [2019-01, 2020-01): single bin -> entropy 0
        self.assertEqual(row["f2_commit_entropy"], 0.0)
        self.assertFalse(row["never_released"])
        # recent window holds bot-published releases only (gaps 183/182d);
        # prior window holds the 2016 human release alone -> median undefined
        self.assertIsNone(row["f1_release_decay"])

    def test_corridor_feature_row_keys(self):
        row = features.feature_row(corridor(), T(2019, 1, 1))
        for key in ("f1_release_decay", "never_released", "f2_commit_entropy",
                    "f3_backlog_slope", "f4_latency_trend", "f5_rate_decline",
                    "f6_maint_volume", "f6_recent_comments", "f6_prior_comments",
                    "bf50", "log10_stars", "age_years", "language_py",
                    "language_js", "created_year"):
            self.assertIn(key, row)


class BuildRowsTest(unittest.TestCase):
    def test_synthetic_cache(self):
        """build_rows joins labels + features over a faked cache; specimen excluded."""
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)

            def write(slug, endpoint, rows):
                path = cache / slug / f"{endpoint}.ndjson"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("".join(json.dumps(r) + "\n" for r in rows))

            # repo A: one ghosting corridor; repo B: the specimen (excluded)
            a = corridor()
            write("fixt__corridor", "meta", [a.meta])
            write("fixt__corridor", "issues", a.issues)
            write("fixt__corridor", "comments", a.comments)
            write("fixt__corridor", "commits", a.commits)
            write("fixt__corridor", "releases", a.releases)
            write("request__request", "meta", [{"full_name": "request/request",
                                                "created_at": "2014-06-01T00:00:00Z"}])

            features.CACHE = cache
            from ofrenda import fetch
            saved = fetch.CACHE
            fetch.CACHE = cache
            try:
                rows, summary = features.build_rows()
            finally:
                fetch.CACHE = saved

            self.assertEqual(summary["repos"], 1)
            self.assertGreater(len(rows), 0)
            self.assertTrue(all(row["repo"] == "fixt/corridor" for row in rows))
            self.assertTrue(all(row["group"] is None for row in rows))
            # every row carries both label and feature columns
            row = rows[0]
            for key in ("y1", "y2", "t", "f1_release_decay", "bf50", "log10_stars"):
                self.assertIn(key, row)
            states = {(r["y1"], r["y2"]) for r in rows}
            self.assertIn((1, 0), states)   # GHOSTING rows exist in the corridor
            self.assertIn((1, 1), states)   # DEAD rows exist (T=2022)
            self.assertIn((0, 0), states)   # ALIVE rows exist (T=2016/2017)
            # corridor rows: 2016 A, 2017 A, 2018-2021 G, 2022 D (7 rows)
            self.assertEqual(summary["y1_base_rate"], round(5 / 7, 4))
            self.assertEqual(summary["y2_base_rate"], round(1 / 7, 4))


if __name__ == "__main__":
    unittest.main()
