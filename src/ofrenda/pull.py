"""Stage 4: discover the corpus roster, then serially pull every repo (PRD §7).

Registered here and in PRD §20 (2026-10-28 19:24, while the probe still runs):

- Cells: language x star-band x created-band. Star bands 100-300, 300-1000,
  1000-3000, 3000+; created bands 2013-2015, 2016-2018, 2019-2020 (age floor:
  nothing created before 2013). Languages: python, javascript only.
- Strata shares fixed at 0.6 dead / 0.2 archived / 0.2 alive (n=300 -> 180/60/
  60; n=150 -> 90/30/30). Language split is 50/50 within each stratum. Alive
  controls are matched on star and age band: each cell gets an alive quota
  proportional to how many dead repos that cell actually supplied
  (largest-remainder rounding); unfilled alive quota redistributes.
- Dead query:  pushed:<2021-01-01 archived:false fork:false <bands>
  Archived:    pushed:<2021-01-01 archived:true  fork:false <bands>
  Alive:       pushed:>2025-06-01 archived:false fork:false <bands>
- Candidates are taken in search-result order, page 1 only (per_page=100).
  A short cell's quota redistributes over cells that still have page-1
  candidates, in fixed cell order.
- Vet at take-time rejects stale-index contradictions: fork flag, the repo's
  own stars/created date falling outside its cell, specimen, duplicates,
  pre-2013 creation, and dead candidates the search index still reports as
  live or recently pushed.
- Pull is serial and journaled (pull_out/journal.ndjson, one row per attempt).
  A repo already journaled ok is skipped without spending a call; a failed
  repo is retried, and fetch_repo refetches only the streams its cache lacks.
  5 consecutive failures abort the run -- a systematic problem, not a one-off.
- Pull order: dead -> archived -> alive, cells in fixed order, so a restart
  repeats the same selection.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import time
from pathlib import Path
from typing import Any

from .fetch import PAGE_CAPS, fetch_repo
from .derive import parse
from .gh import GitHub

OUT_DIR = Path(__file__).resolve().parents[2] / "pull_out"
ROSTER = OUT_DIR / "roster.json"
JOURNAL = OUT_DIR / "journal.ndjson"

SPECIMEN = "request/request"
FAIL_LIMIT = 5
SEARCH_PACE = 2.2  # seconds between search calls (~27/min against 30/min cap)

STAR_BANDS = ((100, 300), (300, 1000), (1000, 3000), (3000, None))
CREATED_BANDS = (
    ("2013-01-01", "2015-12-31"),
    ("2016-01-01", "2018-12-31"),
    ("2019-01-01", "2020-12-31"),
)
LANGUAGES = ("python", "javascript")

CELLS = [
    (lang, star, created)
    for lang in LANGUAGES
    for star in STAR_BANDS
    for created in CREATED_BANDS
]


def strata_quota(n: int) -> tuple[int, int, int]:
    """(dead, archived, alive) counts for a corpus of n, shares 0.6/0.2/0.2."""
    alive = round(0.2 * n)
    archived = round(0.2 * n)
    return n - archived - alive, archived, alive


def quota_even(total: int, buckets: int) -> list[int]:
    """Largest-remainder even split; deterministic bucket order."""
    base, rem = divmod(total, buckets)
    return [base + (1 if i < rem else 0) for i in range(buckets)]


def _cell_str(cell: tuple[str, tuple[float, float | None], tuple[str, str]]) -> str:
    lang, (star_lo, star_hi), (c_lo, c_hi) = cell
    star = f"{star_lo}-{star_hi}" if star_hi else f">={star_lo}"
    return f"{lang}|stars:{star}|created:{c_lo[:4]}-{c_hi[:4]}"


def _star_clause(band: tuple[float, float | None]) -> str:
    lo, hi = band
    if hi is None:
        return f"stars:>={lo}"
    return f"stars:{lo}..{hi - 1}"


def _query(stratum: str, cell: tuple) -> str:
    lang, star_band, created_band = cell
    pushed = "pushed:>2025-06-01" if stratum == "alive" else "pushed:<2021-01-01"
    archived = "archived:true" if stratum == "archived" else "archived:false"
    return " ".join((
        pushed,
        archived,
        "fork:false",
        _star_clause(star_band),
        f"created:{created_band[0]}..{created_band[1]}",
        f"language:{lang}",
    ))


class _Candidates:
    """One search call per cell, page 1 (per_page=100), lazily consumed in order."""

    def __init__(self, gh: GitHub, query: str) -> None:
        self._items = _search_page(gh, query)
        self.pos = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.pos >= len(self._items):
            raise StopIteration
        item = self._items[self.pos]
        self.pos += 1
        return item


def _search_page(gh: GitHub, query: str) -> list[dict[str, Any]]:
    time.sleep(SEARCH_PACE)
    result = gh.get("/search/repositories", {"q": query, "per_page": 100})
    if not isinstance(result, dict):
        return []
    return list(result.get("items") or [])


def _vet(stratum: str, item: dict[str, Any], cell: tuple) -> str | None:
    """Reject stale-index contradictions. Returns a reason or None."""
    if item.get("fork"):
        return "fork"
    stars = item.get("stargazers_count")
    lo, hi = cell[1]
    if not isinstance(stars, int) or not (lo <= stars < (hi if hi else 10**9)):
        return "star-band"
    created = parse(item.get("created_at"))
    c_lo, c_hi = cell[2]
    if created and not (
        dt.date.fromisoformat(c_lo) <= created.date() <= dt.date.fromisoformat(c_hi)
    ):
        return "created-band"
    if stratum == "alive":
        return None
    if bool(item.get("archived")) != (stratum == "archived"):
        return "archived-flag"
    if stratum == "dead":
        pushed = parse(item.get("pushed_at"))
        if not pushed or pushed >= dt.datetime(2021, 1, 1, tzinfo=dt.timezone.utc):
            return "pushed-recent"
    return None


def _fill(
    gh: GitHub,
    stratum: str,
    want_by_cell: dict[tuple, int],
    taken: set[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fill stratum quotas cell-by-cell, then redistribute leftovers."""
    entries: list[dict[str, Any]] = []
    receipts: dict[str, Any] = {}
    pools: dict[tuple, _Candidates] = {}
    queries: dict[tuple, str] = {}
    warn: dict[str, int] = {}
    leftover = 0

    def take(cell: tuple, item: dict[str, Any]) -> None:
        name = item["full_name"]
        taken.add(name)
        entries.append({
            "group": stratum,
            "full_name": name,
            "language": item.get("language"),
            "stars": item.get("stargazers_count"),
            "created_at": item.get("created_at"),
            "pushed_at": item.get("pushed_at"),
            "cell": _cell_str(cell),
        })

    for cell in CELLS:
        query = _query(stratum, cell)
        remaining = want_by_cell.get(cell, 0)
        if not remaining:
            continue
        received = 0
        pool = _Candidates(gh, query)
        pools[cell] = pool
        queries[cell] = query
        for item in pool:
            if not remaining:
                break
            veto = _vet(stratum, item, cell)
            if veto or item.get("full_name") in taken:
                continue
            take(cell, item)
            remaining -= 1
            received += 1
        leftover += remaining
        if received:
            receipts[_cell_str(cell)] = received

    # Redistribution: fixed cell order over cells with unconsumed candidates.
    drained = []
    if leftover:
        for cell in CELLS:
            if not leftover:
                break
            pool = pools.get(cell)
            if pool is None:
                pool = pools[cell] = _Candidates(gh, _query(stratum, cell))
            while leftover:
                item = next(pool, None)
                if item is None:
                    drained.append(cell)
                    break
                veto = _vet(stratum, item, cell)
                if veto or item.get("full_name") in taken:
                    continue
                take(cell, item)
                leftover -= 1
                receipts[_cell_str(cell)] = receipts.get(_cell_str(cell), 0) + 1
    if leftover:
        warn["unfilled"] = leftover

    return entries, {
        "chosen": receipts,
        "queries": { _cell_str(c): q for c, q in queries.items() },
        "want": {_cell_str(c): w for c, w in want_by_cell.items() if w},
        **warn,
    }


def matched_alive_quota(
    dead_counts: dict[tuple, int], alive_total: int
) -> dict[tuple, int]:
    """Alive quota per cell, proportional to the dead cohort's cell counts."""
    if not dead_counts or not alive_total:
        return {cell: 0 for cell in CELLS}
    inner = sum(dead_counts.values())
    exact = {cell: alive_total * n / inner for cell, n in dead_counts.items()}
    quotas = {cell: int(exact.get(cell, 0)) for cell in CELLS}
    remaining = alive_total - sum(quotas.values())
    by_remainder = sorted(
        (cell for cell in dead_counts if cell in quotas),
        key=lambda c: (-(exact[c] - quotas[c]), CELLS.index(c)),
    )
    for cell in by_remainder[:remaining]:
        quotas[cell] += 1
    return quotas


def _want_for_cells(
    total: int, languages: tuple[str, ...], cells_per_language: int
) -> dict[tuple, int]:
    """Split a stratum across languages 50/50 then across its cells evenly."""
    per_language = quota_even(total, len(languages))
    want: dict[tuple, int] = {}
    for index, lang in enumerate(languages):
        cells = [cell for cell in CELLS if cell[0] == lang]
        for cell, value in zip(cells, quota_even(per_language[index], cells_per_language)):
            want[cell] = value
    return want


def discover_roster(gh: GitHub, n: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build the full roster (dead -> archived -> alive) plus receipts."""
    dead_total, archived_total, alive_total = strata_quota(n)
    taken: set[str] = {SPECIMEN}
    roster: list[dict[str, Any]] = []
    receipts: dict[str, Any] = {}
    dead_counts: dict[tuple, int] = {}

    for stratum, total in (("dead", dead_total), ("archived", archived_total)):
        want = _want_for_cells(total, LANGUAGES, len(STAR_BANDS) * len(CREATED_BANDS))
        entries, receipt = _fill(gh, stratum, want, taken)
        roster.extend(entries)
        if stratum == "dead":
            for entry in entries:
                cell = next(c for c in CELLS if _cell_str(c) == entry["cell"])
                dead_counts[cell] = dead_counts.get(cell, 0) + 1
        receipts[stratum] = receipt

    alive_want = matched_alive_quota(dead_counts, alive_total)
    entries, receipt = _fill(gh, "alive", alive_want, taken)
    roster.extend(entries)
    receipts["alive"] = receipt

    return roster, {
        "totals": {"dead": dead_total, "archived": archived_total, "alive": alive_total},
        **receipts,
    }


def read_journal() -> set[str]:
    ok: set[str] = set()
    if not JOURNAL.exists():
        return ok
    with JOURNAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("ok"):
                ok.add(row["repo"])
    return ok


def journal(row: dict[str, Any]) -> None:
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    with JOURNAL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def run(
    gh: GitHub, roster_path: Path | None = None, limit: int | None = None
) -> dict[str, Any]:
    """Serially pull every roster repo; journaled-ok repos cost zero calls."""
    source = roster_path or ROSTER
    plan = json.loads(source.read_text(encoding="utf-8"))
    done = read_journal()
    started = time.time()

    tallies = {group: {"ok": 0, "failed": 0} for group in ("dead", "archived", "alive")}
    truncated = 0
    consecutive = 0
    aborted = False
    fetched_this_run = 0

    for entry in plan["roster"]:
        if limit is not None and fetched_this_run >= limit:
            break
        name = entry["full_name"]
        group = entry["group"]
        if name in done:
            tallies[group]["ok"] += 1
            print(f"[skip] {group:<10} {name} (journaled)")
            continue
        print(f"[pull] {group:<10} {name} ...", flush=True)
        try:
            stat = fetch_repo(gh, name)
        except Exception as exc:  # journal-and-continue; abort is scripted
            stat = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        row = {
            "repo": name,
            "group": group,
            "ok": bool(stat.get("ok")),
            "calls": stat.get("calls"),
            "secs": stat.get("seconds"),
            "truncated": stat.get("truncated", []),
            "error": stat.get("error"),
            "ts": dt.datetime.now().isoformat(timespec="seconds"),
        }
        journal(row)
        if row["ok"]:
            tallies[group]["ok"] += 1
            fetched_this_run += 1
            truncated += len(row["truncated"])
            consecutive = 0
            print(f"       ok — {row['calls']} calls, {row['secs']}s")
        else:
            tallies[group]["failed"] += 1
            consecutive += 1
            print(f"       FAILED: {row['error']}")
            if consecutive >= FAIL_LIMIT:
                aborted = True
                print(f"[abort] {consecutive} consecutive failures — stopping; "
                      "resume re-runs this roster and retries failures")
                break

    summary = {
        "roster": str(source),
        "n": plan.get("n"),
        "tallies": tallies,
        "truncated_streams": truncated,
        "aborted": aborted,
        "core_calls_this_run": gh.calls,
        "wallclock_seconds": round(time.time() - started, 1),
        "caps": PAGE_CAPS,
    }
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=300,
                        help="corpus size (ladder rung; default 300)")
    parser.add_argument("--discover-only", action="store_true",
                        help="write roster.json and exit without pulling")
    parser.add_argument("--roster", type=Path, default=None,
                        help="roster path to reuse instead of pull_out/roster.json")
    parser.add_argument("--fresh", action="store_true",
                        help="re-run discovery even if a matching roster exists")
    parser.add_argument("--limit", type=int, default=None,
                        help="stop after this many successful pulls this run")
    args = parser.parse_args(argv)

    if args.roster is not None and not args.roster.exists():
        raise SystemExit(f"--roster {args.roster}: file not found (discover first)")
    existing = ROSTER if (args.roster is None and not args.fresh) else None
    if existing and existing.exists():
        plan = json.loads(existing.read_text(encoding="utf-8"))
        if plan.get("n") == args.n:
            print(f"roster: reusing {existing} (n={args.n})")
        else:
            existing = None  # roster shape is n-shaped; rebuild
    if not existing:
        gh = GitHub()
        roster, receipts = discover_roster(gh, args.n)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        plan = {"when": dt.datetime.now().isoformat(timespec="seconds"),
                "n": args.n, "receipts": receipts, "roster": roster}
        ROSTER.write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")
        counts = {}
        for entry in roster:
            counts[entry["group"]] = counts.get(entry["group"], 0) + 1
        print(f"roster: {len(roster)} entries for n={args.n} -> {counts}"
              f" (search calls {gh.search_calls})")
        if args.discover_only:
            return 0

    run(GitHub(), args.roster, limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
