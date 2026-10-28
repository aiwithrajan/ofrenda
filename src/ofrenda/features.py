"""Stage 2b: registered features + background controls per (repo, T).

Pure functions over the event cache; rows land in derived/rows.ndjson.
Definitions and arithmetic are pre-registered in PRD §9 and §20 (19:20):

- f1 release-cadence decay: median inter-release interval (days) in
  [T-24mo, T) vs [T-48mo, T-24mo); the never_released indicator rides along.
- f2 commit-interval Shannon entropy (bits) over intervals between HUMAN
  commits in [T-12mo, T), binned in days: <1, 1-3, 3-14, 14-45, 45-120, >=120.
- f4 maintainer response-latency trend: median issue->first-maintainer-
  response latency, recent 12mo vs prior 12mo (both anchored inside
  [T-24mo, T)); a first-response later than T is banned (look-ahead rule).
- f5 response-rate decline: recent_share - prior_share of stranger-opened
  issues answered within their 12-month window. Differences, not ratios.
- f6 maintainer-comment volume ratio, recent vs prior 12mo (divisor 0 ->
  None); both counts emitted descriptively.
- f3 open-issue backlog slope: OLS slope of monthly backlog of human-opened,
  unresolved, non-PR issues over T-11mo..T (descriptive only).
- bf50: number of top human commit authors covering 50% of commits in
  [T-12mo, T).
- Background controls: log10(stars at fetch), age in years at T, one-hot
  language, created-year cohort.

Global ratio convention: denominator 0 -> None. Nothing imputes None; the
fits layer decides how missing features are carried.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import statistics
from pathlib import Path
from typing import Any

from .derive import (
    ANNUAL_GRID,
    MAINTAINER_ASSOC,
    Repo,
    add_months,
    entropy,
    is_bot,
    is_bot_commit,
    load,
    parse,
    rows_for,
)
from .fetch import CACHE

SPECIMEN = "request/request"  # S1: corpse rows are never corpus rows

BINS_DAYS = (
    (0.0, 1.0),
    (1.0, 3.0),
    (3.0, 14.0),
    (14.0, 45.0),
    (45.0, 120.0),
    (120.0, math.inf),
)


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    """Global convention: a zero or missing denominator makes the feature None."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _median_interval_days(stamps: list[dt.datetime]) -> float | None:
    if len(stamps) < 2:
        return None
    gaps = [(b - a).total_seconds() / 86400.0 for a, b in zip(stamps, stamps[1:])]
    return statistics.median(gaps)


def _release_stamps(repo: Repo) -> list[dt.datetime]:
    out = [parse(release.get("published_at")) for release in repo.releases]
    return sorted(when for when in out if when)


def _human_commit_stamps(repo: Repo) -> list[dt.datetime]:
    out = []
    for commit in repo.commits:
        if is_bot_commit(commit):
            continue
        when = parse(((commit.get("commit") or {}).get("author") or {}).get("date"))
        if when:
            out.append(when)
    return sorted(out)


def _maint_comment_stamps(repo: Repo) -> list[dt.datetime]:
    out = []
    for comment in repo.comments:
        if comment.get("author_association") not in MAINTAINER_ASSOC:
            continue
        login = (comment.get("user") or {}).get("login")
        if login is None or is_bot(login):
            continue
        when = parse(comment.get("created_at"))
        if when:
            out.append(when)
    return out


def f1_release_decay(repo: Repo, t: dt.datetime) -> tuple[float | None, bool]:
    """(f1, never_released): median inter-release interval, recent 24mo vs prior 24mo."""
    stamps = _release_stamps(repo)
    recent = _median_interval_days(
        [when for when in stamps if add_months(t, -24) <= when < t]
    )
    prior = _median_interval_days(
        [
            when
            for when in stamps
            if add_months(t, -48) <= when < add_months(t, -24)
        ]
    )
    return _ratio(recent, prior), not stamps


def f2_commit_entropy(repo: Repo, t: dt.datetime) -> float | None:
    """Shannon entropy (bits) of binned intervals between human commits, 12mo."""
    lo = add_months(t, -12)
    inside = [when for when in _human_commit_stamps(repo) if lo <= when < t]
    if len(inside) < 2:
        return None
    gaps = [(b - a).total_seconds() / 86400.0 for a, b in zip(inside, inside[1:])]
    counts = [0] * len(BINS_DAYS)
    for gap in gaps:
        for i, (low, high) in enumerate(BINS_DAYS):
            if low <= gap < high:
                counts[i] += 1
                break
    return entropy(counts)


def _stranger_issues(repo: Repo) -> dict[int, tuple[dt.datetime, str | None]]:
    """Human-opened, non-PR issues: number -> (opened_at, opener login)."""
    prs = repo.pr_numbers
    out: dict[int, tuple[dt.datetime, str | None]] = {}
    for issue in repo.issues:
        if "pull_request" in issue:
            continue
        number = issue.get("number")
        opened = parse(issue.get("created_at"))
        if number is None or opened is None or number in prs:
            continue
        opener = (issue.get("user") or {}).get("login")
        if opener and is_bot(opener):
            continue
        out[int(number)] = (opened, opener)
    return out


def _first_maintainer_responses(repo: Repo) -> dict[int, dt.datetime]:
    """First maintainer response timestamp per issue (stranger answers only)."""
    firsts: dict[int, dt.datetime] = {}
    for when, number in repo.responses():
        previous = firsts.get(number)
        if previous is None or when < previous:
            firsts[number] = when
    return firsts


def f4_f5(repo: Repo, t: dt.datetime) -> tuple[float | None, float | None]:
    """(f4 latency trend ratio, f5 response-rate decline share-difference)."""
    strangers = _stranger_issues(repo)
    firsts = _first_maintainer_responses(repo)
    windows = (
        ("recent", add_months(t, -12), t),
        ("prior", add_months(t, -24), add_months(t, -12)),
    )

    opened_counts: dict[str, int] = {}
    latencies: dict[str, list[float]] = {}
    for name, lo, hi in windows:
        opened: list[int] = []
        lats: list[float] = []
        for number, (opened_at, _opener) in strangers.items():
            if not (lo <= opened_at < hi):
                continue
            opened.append(number)
            response = firsts.get(number)
            # Look-ahead ban: a response is evidence only if it happened
            # before this window's end; later answers stay invisible here.
            if response is not None and response < hi:
                lats.append((response - opened_at).total_seconds() / 86400.0)
        opened_counts[name] = len(opened)
        latencies[name] = lats

    recent_med = statistics.median(latencies["recent"]) if latencies["recent"] else None
    prior_med = statistics.median(latencies["prior"]) if latencies["prior"] else None
    latency_trend = _ratio(recent_med, prior_med)

    recent_share = (
        len(latencies["recent"]) / opened_counts["recent"] if opened_counts["recent"] else None
    )
    prior_share = (
        len(latencies["prior"]) / opened_counts["prior"] if opened_counts["prior"] else None
    )
    decline = None if (recent_share is None or prior_share is None) else prior_share - recent_share
    return latency_trend, decline


def f6_maint_volume(repo: Repo, t: dt.datetime) -> tuple[float | None, int, int]:
    """(f6 ratio, recent count, prior count) of human maintainer comments."""
    stamps = _maint_comment_stamps(repo)
    recent_n = sum(1 for when in stamps if add_months(t, -12) <= when < t)
    prior_n = sum(1 for when in stamps if add_months(t, -24) <= when < add_months(t, -12))
    return _ratio(float(recent_n), float(prior_n)), recent_n, prior_n


def f3_backlog_slope(repo: Repo, t: dt.datetime) -> float | None:
    """OLS slope of monthly human-opened unresolved backlog, T-11mo..T. Descriptive."""
    strangers = _stranger_issues(repo)
    if not strangers:
        return None
    closing: dict[int, dt.datetime] = {}
    for issue in repo.issues:
        closed_at = parse(issue.get("closed_at"))
        number = issue.get("number")
        if closed_at and number is not None:
            closing[int(number)] = closed_at
    points: list[tuple[float, float]] = []
    for step, month_end in enumerate([add_months(t, -k) for k in range(11, -1, -1)]):
        backlog = sum(
            1
            for number, (opened, _opener) in strangers.items()
            if opened <= month_end
            and (number not in closing or closing[number] > month_end)
        )
        points.append((float(step), float(backlog)))
    n = len(points)
    mean_x = sum(x for x, _ in points) / n
    mean_y = sum(y for _, y in points) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in points)
    var = sum((x - mean_x) ** 2 for x, _ in points)
    return cov / var if var else None


def bf50(repo: Repo, t: dt.datetime) -> int | None:
    """Top human commit authors covering 50% of commits in [T-12mo, T)."""
    lo = add_months(t, -12)
    counts: dict[str, int] = {}
    for commit in repo.commits:
        when = parse(((commit.get("commit") or {}).get("author") or {}).get("date"))
        if not when or not (lo <= when < t):
            continue
        login = (commit.get("author") or {}).get("login")
        if not login or is_bot(login):
            continue
        counts[login] = counts.get(login, 0) + 1
    total = sum(counts.values())
    if not total:
        return None
    cumulative = 0
    for rank, count in enumerate(sorted(counts.values(), reverse=True), start=1):
        cumulative += count
        if cumulative * 2 >= total:
            return rank
    return None


def background(repo: Repo, t: dt.datetime) -> dict[str, float | int | None]:
    """Matched-pair controls present in every fit (PRD §9)."""
    created = repo.created_at
    stars = repo.meta.get("stargazers_count") or 0
    language = repo.meta.get("language")
    return {
        "log10_stars": round(math.log10(stars + 1), 4),
        "age_years": (
            round((t - created).total_seconds() / (86400.0 * 365.25), 4) if created else None
        ),
        "language_js": 1 if language == "JavaScript" else 0,
        "language_py": 1 if language == "Python" else 0,
        "created_year": created.year if created else None,
    }


def feature_row(repo: Repo, t: dt.datetime) -> dict[str, Any]:
    """All registered features + controls at one reference date."""
    f1_value, never_released = f1_release_decay(repo, t)
    f4_value, f5_value = f4_f5(repo, t)
    f6_value, f6_recent, f6_prior = f6_maint_volume(repo, t)
    return {
        "f1_release_decay": f1_value,
        "never_released": never_released,
        "f2_commit_entropy": f2_commit_entropy(repo, t),
        "f3_backlog_slope": round(f3_backlog_slope(repo, t), 4)
        if f3_backlog_slope(repo, t) is not None
        else None,
        "f4_latency_trend": f4_value,
        "f5_rate_decline": f5_value,
        "f6_maint_volume": f6_value,
        "f6_recent_comments": f6_recent,
        "f6_prior_comments": f6_prior,
        "bf50": bf50(repo, t),
        **background(repo, t),
    }


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Assemble (repo, T) rows for every cached repo, excluding the specimen.

    Labels come from derive.rows_for (the pre-registered masks + windows);
    features join onto the same T. Pure post-processing of the cache.
    """
    rows: list[dict[str, Any]] = []
    repos: list[str] = []
    for slug in sorted(p.name for p in CACHE.iterdir() if (p / "meta.ndjson").exists()):
        full_name = slug.replace("__", "/")
        if full_name == SPECIMEN:
            continue
        repo = load(full_name)
        if repo is None:
            continue
        repos.append(full_name)
        for label in rows_for(repo, ANNUAL_GRID):
            t = parse(label["t"])
            assert t is not None
            rows.append({"repo": full_name, "group": None, **label, **feature_row(repo, t)})

    def base_rate(column: str) -> float | None:
        if not rows:
            return None
        return round(sum(1 for row in rows if row[column] == 1) / len(rows), 4)

    summary = {
        "repos": len(repos),
        "rows": len(rows),
        "y1_base_rate": base_rate("y1"),
        "y2_base_rate": base_rate("y2"),
        "null_feature_counts": {
            key: sum(1 for row in rows if row.get(key) is None)
            for key in (
                "f1_release_decay",
                "f2_commit_entropy",
                "f3_backlog_slope",
                "f4_latency_trend",
                "f5_rate_decline",
                "f6_maint_volume",
                "bf50",
            )
        },
    }
    return rows, summary


def main() -> int:
    rows, summary = build_rows()
    out = Path(__file__).resolve().parents[2] / "derived"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "rows.ndjson"
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"derive: {summary['rows']} rows over {summary['repos']} repos -> {path}")
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
