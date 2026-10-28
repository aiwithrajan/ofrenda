"""Stage 2: pure functions over cached NDJSON. No network, no side effects.

Labels are derived here and nowhere else, so relabelling is free. Two nested
targets at reference date T over [T, T+18 months):

    y1 = 1  no maintainer answered a stranger's issue      -> P(>= GHOSTING)
    y2 = 1  no human activity of any kind                  -> P(>= DEAD)

y2 = 1 implies y1 = 1, so the targets nest by construction.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass, field
from typing import Any

from .fetch import read

BOT_SUFFIX = "[bot]"
BOT_DENYLIST = {
    "dependabot",
    "dependabot-preview",
    "renovate",
    "renovate-bot",
    "github-actions",
    "semantic-release",
    "greenkeeper",
    "snyk-bot",
    "codecov",
    "stale",
    "imgbot",
}
MAINTAINER_ASSOC = {"OWNER", "MEMBER", "COLLABORATOR"}
WINDOW_MONTHS = 18

# Pre-registered annual reference grid (PRD §20, 2026-10-28 18:32):
# Jan 1 of 2015..2023 — the nine-point grid both the probe and the fits use.
ANNUAL_GRID = [dt.datetime(y, 1, 1, tzinfo=dt.timezone.utc) for y in range(2015, 2024)]


def is_bot(login: str | None) -> bool:
    if not login:
        return True
    lowered = login.lower()
    if lowered.endswith(BOT_SUFFIX):
        return True
    return any(bot in lowered for bot in BOT_DENYLIST)


def _text_is_bot(name: str | None, email: str | None) -> bool:
    """Bot check on raw git identity, for commits with no GitHub-linked user."""
    for field in (name, email):
        if not field:
            continue
        lowered = field.lower()
        if BOT_SUFFIX in lowered:
            return True
        if any(bot in lowered for bot in BOT_DENYLIST):
            return True
    return False


def is_bot_commit(commit: dict[str, Any]) -> bool:
    """Is this commit authored by a bot?

    The GitHub-linked login wins when present. Otherwise fall back to the raw
    git author name/email — automation reveals itself there as a `[bot]`
    substring or a denylisted identity. The committer login is checked when the
    author has no login, so tool-committed work is caught too.
    """
    author_actor = commit.get("author")
    if isinstance(author_actor, dict) and author_actor.get("login"):
        return is_bot(author_actor["login"])
    committer_actor = commit.get("committer")
    if isinstance(committer_actor, dict) and committer_actor.get("login"):
        if is_bot(committer_actor["login"]):
            return True
    git_author = (commit.get("commit") or {}).get("author") or {}
    return _text_is_bot(git_author.get("name"), git_author.get("email"))


def parse(ts: str | None) -> dt.datetime | None:
    if not ts:
        return None
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def add_months(moment: dt.datetime, months: int) -> dt.datetime:
    month = moment.month - 1 + months
    year = moment.year + month // 12
    month = month % 12 + 1
    day = min(moment.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                           31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return moment.replace(year=year, month=month, day=day)


@dataclass
class Repo:
    full_name: str
    meta: dict[str, Any]
    issues: list[dict[str, Any]] = field(default_factory=list)
    comments: list[dict[str, Any]] = field(default_factory=list)
    commits: list[dict[str, Any]] = field(default_factory=list)
    releases: list[dict[str, Any]] = field(default_factory=list)

    @property
    def pr_numbers(self) -> set[int]:
        return {i["number"] for i in self.issues if "pull_request" in i}

    @property
    def issue_opener(self) -> dict[int, str | None]:
        return {i["number"]: (i.get("user") or {}).get("login") for i in self.issues}

    @property
    def created_at(self) -> dt.datetime | None:
        return parse(self.meta.get("created_at"))

    def responses(self) -> list[tuple[dt.datetime, int]]:
        """Maintainer answers to strangers on non-PR issues."""
        prs = self.pr_numbers
        openers = self.issue_opener
        out: list[tuple[dt.datetime, int]] = []
        for comment in self.comments:
            number = int(comment["issue_url"].rsplit("/", 1)[-1])
            if number in prs:
                continue
            author = (comment.get("user") or {}).get("login")
            if is_bot(author):
                continue
            if comment.get("author_association") not in MAINTAINER_ASSOC:
                continue
            if openers.get(number) == author:
                continue
            when = parse(comment.get("created_at"))
            if when:
                out.append((when, number))
        return sorted(out)

    def human_activity(self) -> list[dt.datetime]:
        """Every timestamp where a human did something observable.

        Audit fixes, 2026-10-28 (logged PRD §20): a commit with no
        GitHub-linked login is still human unless the raw git author name/email
        matches a bot pattern — the old code skipped these, producing
        false-DEAD rows for email-only committers. A comment by a deleted or
        ghost account (user = null) counts as human too: an unknowable identity
        is not a bot.
        """
        stamps: list[dt.datetime] = []
        for comment in self.comments:
            login = (comment.get("user") or {}).get("login")
            if login is not None and is_bot(login):
                continue
            when = parse(comment.get("created_at"))
            if when:
                stamps.append(when)
        for commit in self.commits:
            if is_bot_commit(commit):
                continue
            when = parse((commit.get("commit") or {}).get("author", {}).get("date"))
            if when:
                stamps.append(when)
        for release in self.releases:
            if not is_bot((release.get("author") or {}).get("login")):
                when = parse(release.get("published_at"))
                if when:
                    stamps.append(when)
        return sorted(stamps)


def load(full_name: str) -> Repo | None:
    slug = full_name.replace("/", "__")
    meta_rows = read(slug, "meta")
    if not meta_rows:
        return None
    return Repo(
        full_name=full_name,
        meta=meta_rows[0],
        issues=read(slug, "issues") or [],
        comments=read(slug, "comments") or [],
        commits=read(slug, "commits") or [],
        releases=read(slug, "releases") or [],
    )


def labels_at(repo: Repo, reference: dt.datetime) -> tuple[int, int, dict[str, int]]:
    """Returns (y1, y2, counts) for the 18-month window starting at `reference`."""
    end = add_months(reference, WINDOW_MONTHS)
    answered = sum(1 for when, _ in repo.responses() if reference <= when < end)
    active = sum(1 for when in repo.human_activity() if reference <= when < end)
    return (1 if answered == 0 else 0), (1 if active == 0 else 0), {
        "responses": answered,
        "human_events": active,
    }


def rows_for(
    repo: Repo,
    grid: list[dt.datetime],
    activity: list[dt.datetime] | None = None,
    responses: list[tuple[dt.datetime, int]] | None = None,
) -> list[dict[str, Any]]:
    """Masked label rows for a repo over an annual T grid (PRD §8).

    Mask 1: T >= creation + 12 months — features need history.
    Mask 2: >= 1 human event in [T - 12 months, T) — no trivially-DEAD rows.

    Same masks-and-labels math the probe pre-registered (§20, 18:32 / 19:20);
    lifted out of probe.py so features and fits share one implementation.
    """
    if activity is None:
        activity = repo.human_activity()
    if responses is None:
        responses = repo.responses()
    rows: list[dict[str, Any]] = []
    for t in grid:
        if repo.created_at and t < add_months(repo.created_at, 12):
            continue  # mask 1
        lower = add_months(t, -12)
        if not any(lower <= when < t for when in activity):
            continue  # mask 2
        end = add_months(t, WINDOW_MONTHS)
        answered = sum(1 for when, _ in responses if t <= when < end)
        active = sum(1 for when in activity if t <= when < end)
        rows.append({
            "t": t.isoformat(),
            "y1": 0 if answered else 1,
            "y2": 0 if active else 1,
            "responses": answered,
            "human_events": active,
        })
    return rows


def coverage(repo: Repo) -> dict[str, bool]:
    """Which of the registered features are computable at all for this repo."""
    responses = repo.responses()
    strangers = [
        n for n, opener in repo.issue_opener.items()
        if opener and not is_bot(opener) and n not in repo.pr_numbers
    ]
    maintainer_comments = [
        c for c in repo.comments
        if c.get("author_association") in MAINTAINER_ASSOC
        and not is_bot((c.get("user") or {}).get("login"))
    ]
    authors = {}
    for commit in repo.commits:
        login = (commit.get("author") or {}).get("login")
        if login and not is_bot(login):
            authors[login] = authors.get(login, 0) + 1
    total_commits = sum(authors.values())
    ordered = sorted(authors.values(), reverse=True)
    cumulative = 0
    bf50 = None
    for index, count in enumerate(ordered, start=1):
        cumulative += count
        if total_commits and cumulative >= 0.5 * total_commits:
            bf50 = index
            break

    return {
        "f1_release_decay": len(repo.releases) >= 2,
        "f2_commit_entropy": len(repo.commits) >= 2,
        "f3_backlog_slope": len(strangers) >= 1,
        "f4_latency_trend": len(responses) >= 1,
        "f5_response_rate": len(strangers) >= 1,
        "f6_maint_volume": len(maintainer_comments) >= 1,
        "bf50": bf50 is not None,
    }


def entropy(counts: list[int]) -> float:
    total = sum(counts)
    if total <= 0:
        return 0.0
    return -sum((c / total) * math.log(c / total, 2) for c in counts if c > 0)
