"""Stage 1: fetch raw events to NDJSON. Never computes features or labels.

The separation matters: aggregates bake in window choices, so they are expensive
to retract. Raw events let us relabel and re-window for free.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .gh import GitHub, RateLimited

CACHE = Path(__file__).resolve().parents[2] / "cache"

# Pre-registered page caps (PRD §20, 2026-10-28 — before the probe runs).
# Issues and comments are fetched newest-first so a cap truncates at the OLD
# end: capped repos lose early-T rows via mask 2, never late labels. The
# `truncated` flag is retained and reported per repo by the probe.
PAGE_CAPS = {"issues": 40, "comments": 60, "commits": 40, "releases": 5}


def _slug(full_name: str) -> str:
    return full_name.replace("/", "__")


def _write(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")


def read(slug: str, endpoint: str) -> list[dict[str, Any]] | None:
    path = CACHE / slug / f"{endpoint}.ndjson"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def fetch_repo(
    gh: GitHub,
    full_name: str,
    page_caps: dict[str, int] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Fetch one repo's raw event streams. Returns a cost/coverage summary.

    Per-stream page caps (PRD §20); `page_caps` overrides only the streams given.
    """
    slug = _slug(full_name)
    caps = dict(PAGE_CAPS)
    if page_caps:
        caps.update(page_caps)
    started = time.time()
    calls_before = gh.calls

    try:
        meta = gh.get(f"/repos/{full_name}")
    except RateLimited:
        # Distinguish "the API is refusing us" from "the repo is gone" —
        # run 2's probe mislabeled rate-limited repos as not-found (§20 21:22).
        return {"repo": full_name, "ok": False, "error": "rate-limited"}
    if not meta:
        return {"repo": full_name, "ok": False, "error": "repo not found"}

    result: dict[str, Any] = {
        "repo": full_name,
        "ok": True,
        "archived": bool(meta.get("archived")),
        "stars": meta.get("stargazers_count"),
        "created_at": meta.get("created_at"),
        "pushed_at": meta.get("pushed_at"),
        "language": meta.get("language"),
        "has_issues": bool(meta.get("has_issues")),
        "open_issues": meta.get("open_issues_count"),
        "truncated": [],
    }

    streams = {
        "issues": (f"/repos/{full_name}/issues", {"state": "all", "sort": "created", "direction": "desc"}),
        "comments": (f"/repos/{full_name}/issues/comments", {"sort": "created", "direction": "desc"}),
        "commits": (f"/repos/{full_name}/commits", {}),
        "releases": (f"/repos/{full_name}/releases", {}),
    }

    for name, (path, params) in streams.items():
        if not force:
            cached = read(slug, name)
            if cached is not None:
                result[name] = len(cached)
                continue
        rows, truncated = gh.paginate(path, params, max_pages=caps[name])
        if name == "issues" and not rows and (meta.get("open_issues_count") or 0) > 0:
            # An empty issues stream on a repo with open issues means the fetch
            # was neutered (rate limit / transient error) - never cache silence.
            raise RuntimeError(f"{full_name}: issues empty though open_issues={meta.get('open_issues_count')}")
        _write(CACHE / slug / f"{name}.ndjson", rows)
        result[name] = len(rows)
        if truncated:
            result["truncated"].append(name)

    _write(CACHE / slug / "meta.ndjson", [meta])
    result["calls"] = gh.calls - calls_before
    result["seconds"] = round(time.time() - started, 1)
    return result
