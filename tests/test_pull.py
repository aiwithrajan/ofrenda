"""Pull-orchestrator tests: quotas, discovery, journaling, failure abort.

The stub gh synthesizes cell-valid candidates from the query string, so
discovery runs end-to-end without a single network call. fetch_repo is
stubbed the same way.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ofrenda import pull


class QueryTest(unittest.TestCase):
    def test_dead_query(self):
        query = pull._query("dead", ("python", (100, 300), ("2013-01-01", "2015-12-31")))
        self.assertIn("pushed:<2021-01-01", query)
        self.assertIn("archived:false", query)
        self.assertIn("fork:false", query)
        self.assertIn("stars:100..299", query)
        self.assertIn("created:2013-01-01..2015-12-31", query)
        self.assertIn("language:python", query)

    def test_archived_and_alive_queries(self):
        archived = pull._query("archived", ("javascript", (3000, None), ("2019-01-01", "2020-12-31")))
        self.assertIn("archived:true", archived)
        self.assertIn("stars:>=3000", archived)
        alive = pull._query("alive", ("python", (100, 300), ("2013-01-01", "2015-12-31")))
        self.assertIn("pushed:>2025-06-01", alive)
        self.assertIn("archived:false", alive)


class QuotaTest(unittest.TestCase):
    def test_strata_shares(self):
        self.assertEqual(pull.strata_quota(300), (180, 60, 60))
        self.assertEqual(pull.strata_quota(150), (90, 30, 30))
        self.assertEqual(pull.strata_quota(12), (8, 2, 2))
        self.assertEqual(pull.strata_quota(6), (4, 1, 1))

    def test_quota_even(self):
        self.assertEqual(pull.quota_even(5, 2), [3, 2])
        self.assertEqual(pull.quota_even(2, 12), [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(pull.quota_even(0, 4), [0, 0, 0, 0])

    def test_matched_alive_quota_follows_dead_histogram(self):
        cells = pull.CELLS
        dead = {cells[0]: 3, cells[1]: 1}
        quotas = pull.matched_alive_quota(dead, 4)
        self.assertEqual(quotas[cells[0]], 3)
        self.assertEqual(quotas[cells[1]], 1)
        self.assertEqual(sum(quotas.values()), 4)

    def test_matched_alive_quota_empty_histogram(self):
        quotas = pull.matched_alive_quota({}, 7)
        self.assertEqual(sum(quotas.values()), 0)


class StubGH:
    """Synthesizes cell-valid candidates by parsing the query string."""

    def __init__(self):
        self.counter = 0
        self.calls = 0
        self.search_calls = 0

    def get(self, path, params=None):
        self.search_calls += 1
        query = params["q"]
        self.counter += 1
        if "stars:100..299" in query:
            stars = 150
        elif "stars:300..999" in query:
            stars = 500
        elif "stars:1000..2999" in query:
            stars = 1500
        else:
            stars = 4000
        year = 2013 if "created:2013" in query else (
            2016 if "created:2016" in query else 2019)
        lang = "Python" if "language:python" in query else "JavaScript"
        items = []
        for _ in range(3):
            self.counter += 1
            items.append({
                "full_name": f"stub/repo-{self.counter}",
                "stargazers_count": stars,
                "language": lang,
                "created_at": f"{year}-06-05T00:00:00Z",
                "pushed_at": "2019-01-01T00:00:00Z",
                "archived": "archived:true" in query,
                "fork": False,
            })
        return {"items": items}


class DiscoverTest(unittest.TestCase):
    def test_roster_shape(self):
        with mock.patch.object(pull, "SEARCH_PACE", 0.0):
            gh = StubGH()
            roster, receipts = pull.discover_roster(gh, 6)
        counts = {}
        for entry in roster:
            counts[entry["group"]] = counts.get(entry["group"], 0) + 1
            self.assertTrue(entry["full_name"].startswith("stub/"))
            self.assertIn("|stars:", entry["cell"])
        self.assertEqual(counts, {"dead": 4, "archived": 1, "alive": 1})
        # language split inside the dead stratum is 50/50 (2 and 2)
        langs = [e["language"] for e in roster if e["group"] == "dead"]
        self.assertEqual(langs.count("Python"), 2)
        # the specimen can never appear
        self.assertNotIn("request/request", {e["full_name"] for e in roster})

    def test_specimen_vetoed_even_if_search_returns_it(self):
        class SpecimenGH(StubGH):
            def get(self, path, params=None):
                result = super().get(path, params)
                result["items"].append({
                    "full_name": pull.SPECIMEN,
                    "stargazers_count": 150,
                    "language": "Python",
                    "created_at": "2014-06-05T00:00:00Z",
                    "pushed_at": "2019-01-01T00:00:00Z",
                    "archived": False,
                    "fork": False,
                })
                return result

        with mock.patch.object(pull, "SEARCH_PACE", 0.0):
            roster, _ = pull.discover_roster(SpecimenGH(), 6)
        self.assertNotIn(pull.SPECIMEN, {e["full_name"] for e in roster})


class RunTest(unittest.TestCase):
    def _roster_file(self, tmp, names):
        plan = {"n": 6, "roster": [
            {"group": "dead", "full_name": name, "cell": "x"} for name in names
        ]}
        path = Path(tmp) / "roster.json"
        path.write_text(json.dumps(plan))
        return path

    def test_journal_skip_and_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            roster_path = self._roster_file(tmp, ["stub/a", "stub/b", "stub/c"])
            calls = []

            def fake_fetch(gh, name, **kwargs):
                calls.append(name)
                if name == "stub/b":
                    raise RuntimeError("boom")
                return {"ok": True, "calls": 61, "seconds": 9.0}

            with mock.patch.object(pull, "JOURNAL", Path(tmp) / "journal.ndjson"), \
                 mock.patch.object(pull, "REPO_PAUSE", 0.0), \
                 mock.patch.object(pull, "fetch_repo", fake_fetch):
                summary = pull.run(StubGH(), roster_path)
                self.assertFalse(summary["aborted"])
                self.assertEqual(calls, ["stub/a", "stub/b", "stub/c"])
                # rerun: only the failed repo is retried
                summary2 = pull.run(StubGH(), roster_path)
                self.assertEqual(calls, ["stub/a", "stub/b", "stub/c", "stub/b"])

            rows = (Path(tmp) / "journal.ndjson").read_text().strip().splitlines()
            self.assertEqual(len(rows), 4)
            statuses = [json.loads(r)["ok"] for r in rows]
            self.assertEqual(statuses, [True, False, True, False])

    def test_abort_after_five_consecutive_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            names = [f"stub/r{i}" for i in range(6)]
            roster_path = self._roster_file(tmp, names)

            def fake_fetch(gh, name, **kwargs):
                raise RuntimeError("down")

            with mock.patch.object(pull, "JOURNAL", Path(tmp) / "journal.ndjson"), \
                 mock.patch.object(pull, "REPO_PAUSE", 0.0), \
                 mock.patch.object(pull, "fetch_repo", fake_fetch):
                summary = pull.run(StubGH(), roster_path)
            self.assertTrue(summary["aborted"])
            rows = (Path(tmp) / "journal.ndjson").read_text().strip().splitlines()
            self.assertEqual(len(rows), 5)   # stops AT five, never reaches the 6th

    def test_limit_caps_successful_pulls(self):
        with tempfile.TemporaryDirectory() as tmp:
            names = [f"stub/r{i}" for i in range(4)]
            roster_path = self._roster_file(tmp, names)

            def fake_fetch(gh, name, **kwargs):
                return {"ok": True, "calls": 61, "seconds": 9.0}

            with mock.patch.object(pull, "JOURNAL", Path(tmp) / "journal.ndjson"), \
                 mock.patch.object(pull, "REPO_PAUSE", 0.0), \
                 mock.patch.object(pull, "fetch_repo", fake_fetch):
                summary = pull.run(StubGH(), roster_path, limit=2)
            self.assertEqual(summary["tallies"]["dead"]["ok"], 2)


if __name__ == "__main__":
    unittest.main()
