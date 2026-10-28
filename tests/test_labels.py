"""Label + mask tests over synthetic derive.Repo fixtures. Zero API calls.

The fixtures are GitHub-shaped minimal records (the only fields derive reads):
issue {number, created_at, closed_at, user, pull_request?};
comment {issue_url, created_at, user, author_association};
commit {author: {login}|null, commit: {author: {date, name, email}}};
release {author: {login}, published_at}.
"""

import datetime as dt
import unittest

from ofrenda import derive

UTC = dt.timezone.utc


def T(y, m, d, H=0, M=0, S=0):
    return dt.datetime(y, m, d, H, M, S, tzinfo=UTC)


def iso(t):
    return None if t is None else t.isoformat().replace("+00:00", "Z")


def issue(number, created, opener, pr=False, closed_at=None):
    row = {
        "number": number,
        "created_at": iso(created),
        "closed_at": iso(closed_at),
        "user": {"login": opener},
    }
    if pr:
        row["pull_request"] = {
            "url": f"https://api.github.com/repos/fixt/r/pulls/{number}"
        }
    return row


def comment(number, created, login, assoc="NONE"):
    return {
        "issue_url": f"https://api.github.com/repos/fixt/r/issues/{number}",
        "created_at": iso(created),
        "user": {"login": login, "type": "User"} if login else None,
        "author_association": assoc,
    }


def commit(created, login=None, name=None, email=None):
    return {
        "author": {"login": login} if login else None,
        "commit": {
            "author": {
                "date": iso(created),
                "name": name or login or "anon",
                "email": email or f"{login or 'anon'}@users.noreply.github.com",
            }
        },
    }


def release(published, login=None):
    return {
        "published_at": iso(published),
        "author": {"login": login} if login else None,
    }


def repo(name="r", created=T(2014, 1, 1), seed=True, **streams):
    meta = {
        "full_name": f"fixt/{name}",
        "created_at": iso(created),
        "stargazers_count": 42,
        "language": "Python",
        "archived": False,
    }
    commits = list(streams.get("commits", []))
    if seed:
        # A pre-window human commit so mask 2 never masks the fixture itself;
        # it lies outside every [T, T+18mo) label window used in these tests.
        commits.append(commit(T(2017, 6, 1), login="dev"))
    return derive.Repo(
        f"fixt/{name}", meta,
        issues=streams.get("issues", []),
        comments=streams.get("comments", []),
        commits=commits,
        releases=streams.get("releases", []),
    )


def states(rows):
    return [("MASKED" if row is None else
             "ALIVE" if row["y1"] == 0 else
             "GHOSTING" if row["y2"] == 0 else "DEAD") for row in rows]


def corridor():
    """Social death 2018; code echoes (human commits) until Feb 2021.

    - human commits every ~45d from 2015-01-01 to <= 2021-02-10 (login 'edge')
    - one bot commit inside the echo (2020-09-01) - must not hold y2 open
    - maintainer 'keeper' answers strangers only through 2017-06-10
    - releases from 2018-06 on are published by the release bot
    - one ghost comment (user null) and one login-less commit - human
    """
    commits, stamp, last = [], T(2015, 1, 1), T(2021, 2, 10)
    while stamp <= last:
        commits.append(commit(stamp, login="edge"))
        stamp += dt.timedelta(days=45)
    commits.append(commit(T(2018, 3, 3)))                    # login-less: human
    commits.append(commit(T(2020, 9, 1), login="github-actions[bot]"))
    issues = [
        issue(1, T(2016, 6, 5), "stranger1"),
        issue(2, T(2017, 6, 5), "stranger1"),
        issue(3, T(2018, 2, 5), "stranger2"),
        issue(4, T(2019, 2, 5), "stranger2", pr=True),
    ]
    comments = [
        comment(1, T(2016, 6, 8), "keeper", assoc="OWNER"),
        comment(2, T(2017, 6, 10), "keeper", assoc="OWNER"),
        comment(3, T(2018, 4, 1), None),                      # ghost: human
    ]
    releases = [
        release(T(2016, 6, 1), login="keeper"),
        release(T(2018, 6, 1), login="release-bot[bot]"),
        release(T(2019, 6, 1), login="release-bot[bot]"),
        release(T(2020, 6, 1), login="release-bot[bot]"),
    ]
    return repo("corridor", created=T(2014, 6, 1), seed=False, issues=issues,
                comments=comments, commits=commits, releases=releases)


class CorridorTest(unittest.TestCase):
    """The GHOSTING corridor: labels on the annual grid, end to end."""

    @classmethod
    def setUpClass(cls):
        cls.rows = derive.rows_for(corridor(), derive.ANNUAL_GRID)

    def test_state_sequence(self):
        by_t = {row["t"]: row for row in self.rows}
        expected = {
            "2015-01-01T00:00:00+00:00": None,   # mask 1: created 2014-06 + 12mo
            "2016-01-01T00:00:00+00:00": "ALIVE",
            "2017-01-01T00:00:00+00:00": "ALIVE",
            "2018-01-01T00:00:00+00:00": "GHOSTING",  # last answer 2017-06-10
            "2019-01-01T00:00:00+00:00": "GHOSTING",
            "2020-01-01T00:00:00+00:00": "GHOSTING",
            "2021-01-01T00:00:00+00:00": "GHOSTING",  # echo: commit 2021-02
            "2022-01-01T00:00:00+00:00": "DEAD",      # echo ended; bot != human
            "2023-01-01T00:00:00+00:00": None,        # mask 2: silent 2022
        }
        for t, want in expected.items():
            row = by_t.get(t)
            got = None if row is None else (
                "ALIVE" if row["y1"] == 0 else
                "GHOSTING" if row["y2"] == 0 else "DEAD"
            )
            self.assertEqual(got, want, f"T={t}: expected {want}, got {got}")

    def test_nesting_holds_on_every_row(self):
        for row in self.rows:
            self.assertFalse(row["y2"] == 1 and row["y1"] == 0,
                             f"y2=1 must imply y1=1 at {row['t']}")

    def test_counts_are_windowed(self):
        by_t = {row["t"]: row for row in self.rows}
        row = by_t["2017-01-01T00:00:00+00:00"]
        self.assertGreaterEqual(row["responses"], 1)   # answer on 2017-06-10
        self.assertGreaterEqual(row["human_events"], 2)


class MaskTest(unittest.TestCase):
    def test_mask1_needs_twelve_months_of_history(self):
        monthly = [commit(T(2015, m, 10), login="dev") for m in range(6, 13)]
        monthly += [commit(T(2016, m, 10), login="dev") for m in range(1, 7)]
        source = repo(created=T(2015, 3, 10), seed=False, commits=monthly)
        rows = derive.rows_for(source, [T(2015, 6, 1), T(2016, 6, 1)])
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["t"].startswith("2016-06-01"))

    def test_mask2_requires_recent_human_event(self):
        source = repo(created=T(2014, 1, 1), seed=False,
                      commits=[commit(T(2016, 12, 20), login="dev")])
        rows = derive.rows_for(source, [T(2017, 1, 1), T(2018, 1, 1)])
        # T=2017 row survives (event in [2016-01, 2017-01)); T=2018 is masked.
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["y1"], 1)
        self.assertEqual(rows[0]["y2"], 1)   # silent window: DEAD, not masked
        self.assertEqual(rows[0]["human_events"], 0)


class MaintainerAnswerTest(unittest.TestCase):
    def setUp(self):
        self.window = [T(2018, 1, 1)]

    def test_owner_answer_on_stranger_issue(self):
        source = repo(
            issues=[issue(7, T(2018, 6, 5), "stranger")],
            comments=[comment(7, T(2018, 6, 9), "keeper", assoc="OWNER")],
        )
        rows = derive.rows_for(source, self.window)
        self.assertEqual(rows[0]["y1"], 0)
        self.assertEqual(rows[0]["responses"], 1)

    def test_opener_answering_own_issue_is_not_a_response(self):
        source = repo(
            issues=[issue(7, T(2018, 6, 5), "keeper")],
            comments=[comment(7, T(2018, 6, 9), "keeper", assoc="OWNER")],
        )
        rows = derive.rows_for(source, self.window)
        self.assertEqual(rows[0]["y1"], 1)
        self.assertEqual(rows[0]["responses"], 0)

    def test_bot_maintainer_answer_does_not_count(self):
        source = repo(
            issues=[issue(7, T(2018, 6, 5), "stranger")],
            comments=[comment(7, T(2018, 6, 9), "renovate[bot]", assoc="OWNER")],
        )
        rows = derive.rows_for(source, self.window)
        self.assertEqual(rows[0]["y1"], 1)

    def test_ghost_maintainer_comment_is_not_a_response(self):
        source = repo(
            issues=[issue(7, T(2018, 6, 5), "stranger")],
            comments=[comment(7, T(2018, 6, 9), None, assoc="OWNER")],
        )
        rows = derive.rows_for(source, self.window)
        self.assertEqual(rows[0]["y1"], 1)

    def test_pr_comment_is_not_a_response(self):
        source = repo(
            issues=[issue(7, T(2018, 6, 5), "stranger", pr=True)],
            comments=[comment(7, T(2018, 6, 9), "keeper", assoc="OWNER")],
        )
        rows = derive.rows_for(source, self.window)
        self.assertEqual(rows[0]["y1"], 1)

    def test_answer_after_window_misses_the_label(self):
        source = repo(
            issues=[issue(7, T(2018, 6, 5), "stranger")],
            comments=[comment(7, T(2019, 8, 9), "keeper", assoc="OWNER")],  # > 18mo
        )
        rows = derive.rows_for(source, self.window)
        self.assertEqual(rows[0]["y1"], 1)


class HumanActivityTest(unittest.TestCase):
    def test_loginless_commit_and_ghost_comment_count_as_human(self):
        source = repo(commits=[commit(T(2018, 6, 1))],
                      comments=[comment(1, T(2018, 9, 1), None)])
        rows = derive.rows_for(source, [T(2018, 1, 1)])
        self.assertEqual(rows[0]["y2"], 0)
        self.assertEqual(rows[0]["human_events"], 2)

    def test_bot_commit_and_bot_release_do_not_hold_alive(self):
        source = repo(
            commits=[commit(T(2018, 6, 1), login="github-actions[bot]")],
            releases=[release(T(2018, 9, 1), login="release-bot[bot]")],
        )
        rows = derive.rows_for(source, [T(2018, 1, 1)])
        self.assertEqual(rows[0]["y2"], 1)
        self.assertEqual(rows[0]["human_events"], 0)

    def test_human_release_counts(self):
        source = repo(releases=[release(T(2018, 9, 1), login="keeper")])
        rows = derive.rows_for(source, [T(2018, 1, 1)])
        self.assertEqual(rows[0]["y2"], 0)


class BotCommitTest(unittest.TestCase):
    def test_variants(self):
        cases = [
            (commit(T(2018, 1, 1), login="github-actions[bot]"), True),
            (commit(T(2018, 1, 1), login="renovate"), True),
            (commit(T(2018, 1, 1), login=None, name="deploy[bot]"), True),
            (commit(T(2018, 1, 1), login=None,
                    name="Alice", email="renovate@tidelift.com"), True),
            (commit(T(2018, 1, 1), login=None, name="Alice",
                    email="alice@example.com"), False),
            (commit(T(2018, 1, 1), login="edge"), False),
            # no author actor at all; the committer actor is the bot: tool work
            ({"author": None,
              "commit": {"author": {"date": iso(T(2018, 1, 1)),
                                    "name": "Alice", "email": "a@b.c"}},
              "committer": {"login": "greenkeeper"}}, True),
        ]
        for payload, want in cases:
            self.assertEqual(derive.is_bot_commit(payload), want, payload)


if __name__ == "__main__":
    unittest.main()
