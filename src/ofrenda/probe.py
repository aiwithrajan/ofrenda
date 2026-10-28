"""Stage 0-probe: break the pipeline on awkward repos before the full pull.

Pre-registered in PRD §13 + §20 (2026-10-28, before any label was printed):

- Roster: 15 archetypes (3 each: issues-disabled, zero-releases, bot-maintainer,
  single-commit, archived) + 5 known-alive controls + the corpse
  `request/request`, which front-loads its ingest while remaining excluded
  from every fit regardless.
- T grid: Jan 1 of 2015..2023, annual. Masks apply BEFORE any label prints:
  T >= creation + 12 months, and >= 1 human event in [T-12mo, T).
- Labels are frozen before printing. no threshold tuning after the first look.
- Page caps 40/60/40/5 pages of 100, newest-first; truncation is flagged and
  reported per repo.
- Kill-switch: median core calls/repo > 90 => descope the corpus 300 -> 150.
  The pull is rate-bound, so calls per repo - not wall-clock - predicts the
  schedule.

Stdlib only (gh/fetch/derive are stdlib-only too), so this runs `--no-deps`.
"""

from __future__ import annotations

import datetime as dt
import json
import statistics
import time
from pathlib import Path
from typing import Any

from .derive import Repo, add_months, coverage, is_bot_commit, load, parse
from .fetch import fetch_repo
from .gh import GitHub

OUT_DIR = Path(__file__).resolve().parents[2] / "probe_out"
GRID = [dt.datetime(y, 1, 1, tzinfo=dt.timezone.utc) for y in range(2015, 2024)]
MIX_T = dt.datetime(2023, 1, 1, tzinfo=dt.timezone.utc)
KILL_SWITCH = 90  # median core calls/repo threshold (§13)

COVERAGE_KEYS = [
    "f1_release_decay",
    "f2_commit_entropy",
    "f3_backlog_slope",
    "f4_latency_trend",
    "f5_response_rate",
    "f6_maint_volume",
    "bf50",
]

# Fixed rows: known-alive controls, bot-maintainer cases, and the corpse.
# Search-discovered archetypes are appended by build_roster().
FIXED = [
    ("control", "psf/requests"),
    ("control", "pallets/flask"),
    ("control", "expressjs/express"),
    ("control", "axios/axios"),
    ("control", "tiangolo/fastapi"),
    ("bot-maintainer", "renovatebot/renovate"),
    ("bot-maintainer", "semantic-release/semantic-release"),
    ("bot-maintainer", "dependabot/dependabot-core"),
    ("corpse", "request/request"),
]


# ----------------------------------------------------------------- discovery


def _search(gh: GitHub, query: str) -> list[dict[str, Any]]:
    """One search call (30 req/min core-independent budget)."""
    time.sleep(2.2)
    result = gh.get("/search/repositories", {"q": query, "per_page": 100})
    if not isinstance(result, dict):
        return []
    return list(result.get("items") or [])


def discover_archived(gh: GitHub, limit: int = 3) -> list[str]:
    names: list[str] = []
    queries = (
        "archived:true stars:>100 pushed:<2021-01-01 language:python",
        "archived:true stars:>100 pushed:<2021-01-01 language:javascript",
    )
    for query in queries:
        if len(names) >= limit:
            break
        for item in _search(gh, query):
            name = item.get("full_name")
            if name and name not in names:
                names.append(name)
            if len(names) >= limit:
                break
    return names[:limit]


def discover_issues_disabled(gh: GitHub, limit: int = 3) -> list[str]:
    """Search result items carry `has_issues`, so this costs zero meta calls."""
    names: list[str] = []
    queries = (
        "topic:awesome stars:>100 language:python",
        "topic:awesome stars:>100 language:javascript",
        "stars:>300 pushed:<2020-01-01 language:python",
    )
    for query in queries:
        if len(names) >= limit:
            break
        for item in _search(gh, query):
            full = item.get("full_name")
            if item.get("has_issues") is False and full and full not in names:
                names.append(full)
            if len(names) >= limit:
                break
    return names[:limit]


def discover_zero_release(gh: GitHub, limit: int = 3, max_scans: int = 12) -> list[str]:
    """Small repos rarely ship releases; confirm via the releases endpoint."""
    names: list[str] = []
    scanned = 0
    seen: set[str] = set()
    queries = (
        "stars:100..400 size:<30 pushed:<2019-01-01 language:python",
        "stars:100..400 size:<30 pushed:<2019-01-01 language:javascript",
    )
    for query in queries:
        if len(names) >= limit or scanned >= max_scans:
            break
        for item in _search(gh, query):
            full = item.get("full_name")
            if not full or full in seen:
                continue
            seen.add(full)
            scanned += 1
            releases = gh.get(f"/repos/{full}/releases", {"per_page": 1})
            if releases == []:
                names.append(full)
            if len(names) >= limit or scanned >= max_scans:
                break
    return names[:limit]


def discover_single_commit(gh: GitHub, limit: int = 3, max_scans: int = 14) -> list[str]:
    """Asking a commits page for 2 items and receiving 1 means exactly one commit."""
    names: list[str] = []
    scanned = 0
    seen: set[str] = set()
    queries = (
        "size:<8 stars:50..500 pushed:<2019-01-01 language:python",
        "size:<8 stars:50..500 pushed:<2019-01-01 language:javascript",
    )
    for query in queries:
        if len(names) >= limit or scanned >= max_scans:
            break
        for item in _search(gh, query):
            full = item.get("full_name")
            if not full or full in seen:
                continue
            seen.add(full)
            scanned += 1
            commits = gh.get(f"/repos/{full}/commits", {"per_page": 2})
            if isinstance(commits, list) and len(commits) == 1:
                names.append(full)
            if len(names) >= limit or scanned >= max_scans:
                break
    return names[:limit]


def build_roster(gh: GitHub) -> tuple[list[tuple[str, str]], dict[str, Any]]:
    roster = list(FIXED)
    taken = {name for _, name in roster}
    receipts: dict[str, Any] = {}

    def add(group: str, found: list[str]) -> None:
        chosen = [name for name in found if name not in taken][:3]
        for name in chosen:
            roster.append((group, name))
            taken.add(name)
        receipts[group] = {"candidates": found, "chosen": chosen}

    add("archived", discover_archived(gh))
    add("issues-disabled", discover_issues_disabled(gh))
    add("zero-releases", discover_zero_release(gh))
    add("single-commit", discover_single_commit(gh))
    return roster, receipts


# ------------------------------------------------------------------- analysis


def cache_span(repo: Repo) -> dict[str, str | None]:
    """First/last cached event dates across all four streams."""
    stamps: list[dt.datetime] = []
    for issue in repo.issues:
        when = parse(issue.get("created_at"))
        if when:
            stamps.append(when)
    for comment in repo.comments:
        when = parse(comment.get("created_at"))
        if when:
            stamps.append(when)
    for commit in repo.commits:
        when = parse(((commit.get("commit") or {}).get("author") or {}).get("date"))
        if when:
            stamps.append(when)
    for release in repo.releases:
        when = parse(release.get("published_at"))
        if when:
            stamps.append(when)
    if not stamps:
        return {"from": None, "to": None}
    return {"from": min(stamps).date().isoformat(), "to": max(stamps).date().isoformat()}


def evaluate(gh: GitHub, group: str, name: str) -> dict[str, Any]:
    """Fetch one repo, derive labels on its T grid, and gather probe evidence."""
    try:
        fetch = fetch_repo(gh, name)
    except Exception as exc:  # the probe must keep moving; record and continue
        return {
            "group": group, "repo": name, "ok": False,
            "error": f"fetch failed: {type(exc).__name__}: {exc}",
        }
    if not fetch.get("ok"):
        return {
            "group": group, "repo": name, "ok": False,
            "error": f"fetch failed: {fetch.get('error', 'unknown')}",
        }
    try:
        repo = load(name)
    except Exception as exc:
        return {
            "group": group, "repo": name, "ok": False,
            "error": f"cache read failed: {type(exc).__name__}: {exc}",
        }
    if repo is None:
        return {
            "group": group, "repo": name, "ok": False,
            "error": "no cached meta after fetch",
        }

    activity = repo.human_activity()
    responses = repo.responses()

    def label_window(t: dt.datetime) -> tuple[int, int, dict[str, int]]:
        start, end = t, add_months(t, 18)
        answered = sum(1 for when, _ in responses if start <= when < end)
        active = sum(1 for when in activity if start <= when < end)
        return (0 if answered else 1), (0 if active else 1), {
            "responses": answered, "human_events": active,
        }

    rows: list[dict[str, Any]] = []
    for t in GRID:
        if repo.created_at and t < add_months(repo.created_at, 12):
            continue  # mask 1: features need 12 months of history
        lower = add_months(t, -12)
        if not any(lower <= when < t for when in activity):
            continue  # mask 2: no trivially-DEAD rows free of any event
        y1, y2, counts = label_window(t)
        rows.append({"t": t.isoformat(), "y1": y1, "y2": y2, **counts})

    # §11 dry-run: labels at the archive-anchored reference dates.
    anchors: list[dict[str, Any]] = []
    archived_at = parse(repo.meta.get("archived_at"))
    if archived_at:
        for months in (-36, -18):
            t = add_months(archived_at, months)
            y1, y2, counts = label_window(t)
            anchors.append({
                "t": t.date().isoformat(),
                "months_before_archive": -months,
                "y1": y1, "y2": y2, **counts,
                "mask1": bool(
                    repo.created_at is None or t >= add_months(repo.created_at, 12)
                ),
                "mask2": any(add_months(t, -12) <= w < t for w in activity),
            })

    commit_total = len(repo.commits)
    bot_commits = sum(1 for commit in repo.commits if is_bot_commit(commit))
    return {
        "group": group,
        "repo": name,
        "ok": True,
        "archived": bool(repo.meta.get("archived")),
        "archived_at": repo.meta.get("archived_at"),
        "stars": repo.meta.get("stargazers_count"),
        "language": repo.meta.get("language"),
        "created_at": repo.meta.get("created_at"),
        "has_issues": bool(repo.meta.get("has_issues")),
        "streams": {
            key: fetch.get(key) for key in ("issues", "comments", "commits", "releases")
        },
        "truncated": fetch.get("truncated", []),
        "calls": fetch.get("calls"),
        "seconds": fetch.get("seconds"),
        "span": cache_span(repo),
        "bot_commit_share": round(bot_commits / commit_total, 3) if commit_total else None,
        "login_none_commits": sum(
            1 for commit in repo.commits if not ((commit.get("author") or {}).get("login"))
        ),
        "ghost_comments": sum(
            1 for comment in repo.comments if not ((comment.get("user") or {}).get("login"))
        ),
        "coverage": coverage(repo),
        "rows": rows,
        "archived_anchors": anchors,
    }


# ----------------------------------------------------------------- reporting


def print_roster(repo_rows: list[dict[str, Any]]) -> None:
    print("\n[1] ROSTER FETCH — streams (rows of 100), truncation flags, cost")
    print(f"    {'group':<16}{'repo':<34}{'iss':>5}{'cmt':>6}{'com':>6}{'rel':>5}"
          f"{'calls':>7}{'secs':>7}  truncated")
    for stat in repo_rows:
        if not stat.get("ok"):
            print(f"    {stat['group']:<16}{stat['repo']:<34}  FAILED: {stat.get('error')}")
            continue
        streams = stat["streams"]
        flags = ",".join(stat["truncated"]) or "-"
        print(f"    {stat['group']:<16}{stat['repo']:<34}"
              f"{streams['issues']:>5}{streams['comments']:>6}{streams['commits']:>6}"
              f"{streams['releases']:>5}{stat['calls']:>7}{stat['seconds']:>6}s  {flags}")
        if stat["span"]["from"]:
            print(f"        cached event span {stat['span']['from']} .. {stat['span']['to']}")


def print_coverage(repo_rows: list[dict[str, Any]]) -> None:
    print("\n[2] COVERAGE — is each registered feature computable for this repo?")
    print(f"    {'repo':<34}" + "".join(f"{key.split('_')[0]:>7}" for key in COVERAGE_KEYS))
    for stat in repo_rows:
        if not stat.get("ok"):
            continue
        marks = "".join(
            "    +" if stat["coverage"][key] else "    ·" for key in COVERAGE_KEYS
        )
        print(f"    {stat['repo']:<34}{marks}")
    totals = [
        sum(1 for stat in repo_rows if stat.get("ok") and stat["coverage"][key])
        for key in COVERAGE_KEYS
    ]
    print(f"    {'computable (n of 21)':<34}" + "".join(f"{n:>7}" for n in totals))


def print_mix(repo_rows: list[dict[str, Any]]) -> None:
    rows_at = [
        row for stat in repo_rows if stat.get("ok")
        for row in stat["rows"] if row["t"] == MIX_T.isoformat()
    ]
    alive = sum(1 for row in rows_at if row["y1"] == 0)
    ghost = sum(1 for row in rows_at if row["y1"] == 1 and row["y2"] == 0)
    dead = sum(1 for row in rows_at if row["y2"] == 1)
    print(f"\n[3] LABEL MIX at T = {MIX_T.date().isoformat()} (post-mask rows only)")
    print(f"    unmasked rows at T: {len(rows_at)} of {len(FIXED) + 12} repos")
    print(f"    ALIVE (y1=0):          {alive}")
    print(f"    GHOSTING (y1=1,y2=0):  {ghost}")
    print(f"    DEAD (y2=1):           {dead}")
    for stat in repo_rows:
        if not stat.get("ok"):
            continue
        for row in stat["rows"]:
            if row["t"] != MIX_T.isoformat():
                continue
            state = "ALIVE" if row["y1"] == 0 else ("GHOSTING" if row["y2"] == 0 else "DEAD")
            print(f"    {stat['repo']:<34}{state:<9}"
                  f"y1={row['y1']} y2={row['y2']}"
                  f" (responses={row['responses']}, human_events={row['human_events']})")


def print_grid(repo_rows: list[dict[str, Any]]) -> None:
    print("\n[4] GRID — post-mask rows and y2 prevalence across Jan 1 2015..2023")
    print(f"    {'T':<12}{'rows':>6}{'y1=1':>6}{'y2=1':>6}{'y2/rows':>9}")
    for t in GRID:
        rows = [
            row for stat in repo_rows if stat.get("ok")
            for row in stat["rows"] if row["t"] == t.isoformat()
        ]
        if not rows:
            continue
        y1_count = sum(1 for row in rows if row["y1"] == 1)
        y2_count = sum(1 for row in rows if row["y2"] == 1)
        frac = y2_count / len(rows)
        print(f"    {t.date().isoformat():<12}{len(rows):>6}{y1_count:>6}{y2_count:>6}"
              f"{frac:>9.2f}")


def print_invariants(repo_rows: list[dict[str, Any]]) -> None:
    total_rows = sum(len(stat["rows"]) for stat in repo_rows if stat.get("ok"))
    violations = sum(
        1 for stat in repo_rows if stat.get("ok")
        for row in stat["rows"] if row["y2"] == 1 and row["y1"] == 0
    )
    login_none = sum(
        stat.get("login_none_commits", 0) for stat in repo_rows if stat.get("ok")
    )
    ghost_comments = sum(
        stat.get("ghost_comments", 0) for stat in repo_rows if stat.get("ok")
    )
    controls = [stat for stat in repo_rows if stat.get("ok") and stat["group"] == "control"]
    alive_any = sum(
        1 for stat in controls
        if any(row["y1"] == 0 or row["y2"] == 0 for row in stat["rows"])
    )
    print("\n[5] INVARIANTS — printed before any evaluation uses these labels")
    print(f"    derived rows (post-mask): {total_rows}")
    print(f"    monotonicity violations (y2=1 & y1=0): {violations}  (expected 0)")
    print(f"    login-None commits seen: {login_none}"
          "  (now counted human unless git-level identity is a bot)")
    print(f"    ghost-user comments seen: {ghost_comments}  (counted human)")
    bot_repos = [stat for stat in repo_rows if stat.get("ok") and stat["group"] == "bot-maintainer"]
    for stat in bot_repos:
        print(f"    bot share of commits — {stat['repo']:<38}{stat['bot_commit_share']}")
    print(f"    known-alive controls with >=1 ALIVE/GHOSTING row: {alive_any} of {len(controls)}"
          "  (if 0, the label derivation is broken)")


def print_anchors(repo_rows: list[dict[str, Any]]) -> None:
    print("\n[6] ARCHIVED ANCHORS — §11 dry-run (arch −36mo primary, −18mo sanity)")
    anchored = [stat for stat in repo_rows if stat.get("ok") and stat["archived_at"]]
    if not anchored:
        print("    (no archived repos were fetched)")
    for stat in anchored:
        print(f"    {stat['repo']:<38} archived {str(stat['archived_at'])[:10]}")
        for anchor in stat["archived_anchors"]:
            print(f"        T={anchor['t']} (−{anchor['months_before_archive']:>2}mo)"
                  f"  y1={anchor['y1']} y2={anchor['y2']}"
                  f"  mask1={anchor['mask1']} mask2={anchor['mask2']}")


def print_switch(repo_rows: list[dict[str, Any]]) -> dict[str, Any]:
    calls = [
        stat["calls"] for stat in repo_rows
        if stat.get("ok") and isinstance(stat.get("calls"), int)
    ]
    print("\n[7] KILL-SWITCH (§13) — calls per repo decide, not optimism")
    if not calls:
        print("    no successful fetches — probe failed structurally")
        return {"median": None, "verdict": "PROBE FAILED"}
    median = statistics.median(calls)
    projected_300 = median * 300 / 5000  # 5,000 core calls/hour
    projected_150 = median * 150 / 5000
    verdict = "KEEP n=300" if median <= KILL_SWITCH else "DESCOPE → n=150"
    print(f"    calls/repo: min={min(calls)} median={median:.0f} max={max(calls)}"
          f"  (n={len(calls)} repos)")
    print(f"    projected full pull: n=300 → {projected_300:.1f} h;"
          f" n=150 → {projected_150:.1f} h (rate-bound)")
    print(f"    pre-registered threshold {KILL_SWITCH}: {verdict}")
    return {
        "min": min(calls),
        "median": median,
        "max": max(calls),
        "n": len(calls),
        "threshold": KILL_SWITCH,
        "projected_hours_300": round(projected_300, 2),
        "projected_hours_150": round(projected_150, 2),
        "verdict": verdict,
    }


# ----------------------------------------------------------------------- main


def main() -> int:
    started = time.time()
    gh = GitHub()
    print(f"OFRENDA PROBE — {dt.datetime.now().isoformat(timespec='seconds')}")
    print("PRD §13 + §20 prereg: T grid Jan 1 2015..2023 · caps 40/60/40/5, newest-first"
          " · masks before labels · kill-switch = median > 90 calls/repo")

    roster, receipts = build_roster(gh)
    for group, receipt in receipts.items():
        chosen = receipt["chosen"]
        print(f"[discovery] {group:<16} {len(chosen)}/3 chosen"
              f" -> {', '.join(chosen) if chosen else '(none found)'}")
    print("[discovery] fixed rows: controls x5, bot-maintainer x3, corpse x1")

    repo_rows: list[dict[str, Any]] = []
    for group, name in roster:
        print(f"[fetch] {group:<16} {name} ...", flush=True)
        stat = evaluate(gh, group, name)
        repo_rows.append(stat)
        if not stat.get("ok"):
            print(f"        FAILED: {stat.get('error')}")
        else:
            print(f"        ok — {stat['calls']} calls, {stat['seconds']}s"
                  f" (cache {stat['span']['from']} .. {stat['span']['to']})")

    print_roster(repo_rows)
    print_coverage(repo_rows)
    print_mix(repo_rows)
    print_grid(repo_rows)
    print_invariants(repo_rows)
    print_anchors(repo_rows)
    kill = print_switch(repo_rows)

    summary = {
        "when": dt.datetime.now().isoformat(timespec="seconds"),
        "config": {
            "grid": [t.date().isoformat() for t in GRID],
            "mix_t": MIX_T.date().isoformat(),
            "page_caps": {"issues": 40, "comments": 60, "commits": 40, "releases": 5},
            "kill_switch_median_calls_per_repo": KILL_SWITCH,
        },
        "gh": {
            "core_calls": gh.calls,
            "search_calls": gh.search_calls,
            "remaining": gh.remaining,
        },
        "discovery": receipts,
        "repos": repo_rows,
        "kill_switch": kill,
        "wallclock_seconds": round(time.time() - started, 1),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "probe_summary.json"
    path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"\nwrote {path}")
    print(f"probe wall-clock {round(time.time() - started, 1)}s;"
          f" core calls {gh.calls}; search calls {gh.search_calls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
