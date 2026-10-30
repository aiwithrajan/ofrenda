"""Minimal GitHub REST client.

Auth comes from GITHUB_TOKEN, GH_TOKEN, or `gh auth token` (verified working on
this machine: 5000 core/hr, 30 search/min). Stdlib only so the probe runs with
zero installs.
"""

from __future__ import annotations

import http.client
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"


class RateLimited(RuntimeError):
    """403/429 retries exhausted. None from get() now means a genuine 404/422.

    Probe run 2 finding (PRD §20, 21:22): sustained secondary-limit 403s
    exhausted the old 4-retry budget and came back as None, which the fetch
    layer misreported as "repo not found" for repos that exist. Rate limiting
    is its own failure mode now, not a lookup miss.
    """


def resolve_token() -> str:
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(var)
        if value:
            return value.strip()
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, check=True, timeout=15
        )
        token = out.stdout.strip()
        if token:
            return token
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    raise SystemExit(
        "No GitHub token found. Run `gh auth login`, or export GITHUB_TOKEN."
    )


class GitHub:
    """Rate-limit aware client. Counts calls so the probe can report cost/repo."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token or resolve_token()
        self.calls = 0
        self.search_calls = 0
        self.remaining: int | None = None
        self.reset_at: float | None = None

    def _request(self, url: str) -> tuple[object, dict]:
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ofrenda-probe",
            },
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode("utf-8")
            headers = dict(resp.headers)
            return json.loads(body), headers

    def _wait_if_needed(self) -> None:
        if self.remaining is None or self.remaining > 50:
            return
        if self.reset_at is None:
            time.sleep(5)
            return
        wait = max(1.0, self.reset_at - time.time() + 1)
        if wait < 120:
            print(f"    rate limit low ({self.remaining}); sleeping {wait:.0f}s")
            time.sleep(wait)

    def get(self, path: str, params: dict | None = None, retries: int = 8):
        url = API + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        is_search = "/search/" in path
        for attempt in range(retries):
            self._wait_if_needed()
            try:
                data, headers = self._request(url)
                if is_search:
                    self.search_calls += 1
                else:
                    self.calls += 1
                    # Search has its own per-minute budget; feeding its headers
                    # into the core limiter stalls every core call artificially.
                    rem = headers.get("X-RateLimit-Remaining")
                    rst = headers.get("X-RateLimit-Reset")
                    if rem is not None:
                        self.remaining = int(rem)
                    if rst is not None:
                        self.reset_at = float(rst)
                return data
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    return None
                if exc.code in (403, 429):
                    headers = exc.headers or {}
                    remain = headers.get("X-RateLimit-Remaining")
                    retry_after = headers.get("Retry-After")
                    reset = headers.get("X-RateLimit-Reset")
                    if remain == "0" and reset:
                        wait = max(1.0, float(reset) - time.time() + 2)
                        print(f"    core budget exhausted; sleeping {wait:.0f}s to reset", flush=True)
                        time.sleep(wait)
                        continue
                    # Secondary limits: honor Retry-After (capped), else back off
                    # hard — episodes outlast the old 60 s ceiling (GitHub secondary block needs >=60s).
                    wait = float(retry_after) if retry_after else max(60.0, 30.0 * (attempt + 1))
                    print(f"    secondary limit hit; sleeping {wait:.0f}s (attempt {attempt+1}/{retries})", flush=True)
                    time.sleep(min(180, wait))
                    continue
                if exc.code == 422:
                    return None
                raise
            except (
                urllib.error.URLError,
                TimeoutError,
                ConnectionError,
                http.client.HTTPException,
            ):
                # HTTPException covers IncompleteRead/RemoteDisconnected: big
                # JSON payloads die mid-read on flaky links; retry, don't abort.
                time.sleep(2 ** attempt)
        raise RateLimited(f"{path}: 403/429 on every attempt ({retries})")

    def paginate(
        self,
        path: str,
        params: dict | None = None,
        max_pages: int = 10,
        per_page: int = 100,
    ) -> tuple[list, bool]:
        """Returns (items, truncated). truncated=True means the page cap was hit."""
        items: list = []
        base = dict(params or {})
        base["per_page"] = per_page
        for page in range(1, max_pages + 1):
            base["page"] = page
            batch = self.get(path, base)
            if batch is None and page > 1:
                # A stream that dies mid-pagination is an anomaly (rate limit,
                # transient network) - returning "empty" would cache silence.
                raise RuntimeError(f"{path}: stream broke mid-pagination at page {page}")
            if not batch:
                return items, False
            items.extend(batch)
            if len(batch) < per_page:
                return items, False
            time.sleep(1.2)  # pacing: secondary limits punish bursts (§20 21:22, 2026-10-30)
        return items, True
