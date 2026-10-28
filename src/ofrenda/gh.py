"""Minimal GitHub REST client.

Auth comes from GITHUB_TOKEN, GH_TOKEN, or `gh auth token` (verified working on
this machine: 5000 core/hr, 30 search/min). Stdlib only so the probe runs with
zero installs.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"


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

    def get(self, path: str, params: dict | None = None, retries: int = 4):
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
                    time.sleep(min(60, 2 ** attempt * 5))
                    continue
                if exc.code == 422:
                    return None
                raise
            except (urllib.error.URLError, TimeoutError):
                time.sleep(2 ** attempt)
        return None

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
            if not batch:
                return items, False
            items.extend(batch)
            if len(batch) < per_page:
                return items, False
        return items, True
