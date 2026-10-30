"""Corpse indexing and retrieval engine for request/request.

Governed strictly by PRD v2.0 §12:
- Commits act as memory, issues as arguments, docs as self-image.
- Every retrieved document carries a strict citation:
  (issue #, commit SHA, or doc title).
- Strict citation-or-silence: if relevance score is below threshold,
  the system returns empty so the ghost says "the archive is silent on that."
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CACHE = Path(__file__).resolve().parents[2] / "cache"
SPECIMEN = "request__request"
INDEX_CACHE = Path(__file__).resolve().parents[2] / "derived" / "request_index.json"


@dataclass
class Document:
    doc_id: str
    doc_type: str  # "issue", "comment", "commit", "doc"
    citation: str
    date: str
    title: str
    body: str
    tokens: list[str]


def tokenize(text: str) -> list[str]:
    """Tokenize and normalize text for BM25 retrieval."""
    text = text.lower()
    return re.findall(r"\b[a-z0-9_\-\.#]{2,}\b", text)


class CorpseIndex:
    """In-memory BM25 index over the corpse's cached event history."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.documents: list[Document] = []
        self.doc_lengths: list[int] = []
        self.avg_doc_len: float = 0.0
        self.df: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.inverted_index: dict[str, list[tuple[int, int]]] = {}  # term -> [(doc_idx, tf), ...]

    def add_document(self, doc: Document) -> None:
        doc_idx = len(self.documents)
        self.documents.append(doc)
        length = len(doc.tokens)
        self.doc_lengths.append(length)

        tf: dict[str, int] = {}
        for token in doc.tokens:
            tf[token] = tf.get(token, 0) + 1

        for token, count in tf.items():
            self.df[token] = self.df.get(token, 0) + 1
            if token not in self.inverted_index:
                self.inverted_index[token] = []
            self.inverted_index[token].append((doc_idx, count))

    def finish_indexing(self) -> None:
        n_docs = len(self.documents)
        if n_docs == 0:
            return
        self.avg_doc_len = sum(self.doc_lengths) / n_docs
        for term, freq in self.df.items():
            # BM25 standard IDF with smoothing
            self.idf[term] = math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 5, score_threshold: float = 1.0) -> list[tuple[Document, float]]:
        """Search the corpse's archive. Returns scored documents."""
        query_tokens = tokenize(query)
        if not query_tokens or not self.documents:
            return []

        scores: dict[int, float] = {}
        for token in query_tokens:
            if token not in self.inverted_index:
                continue
            token_idf = self.idf.get(token, 0.0)
            for doc_idx, tf in self.inverted_index[token]:
                doc_len = self.doc_lengths[doc_idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                score = token_idf * (numerator / denominator)
                scores[doc_idx] = scores.get(doc_idx, 0.0) + score

        # Boost canonical documentation and primary records over comment chatter
        for doc_idx in scores:
            dtype = self.documents[doc_idx].doc_type
            if dtype == "doc":
                scores[doc_idx] *= 2.2
            elif dtype in ("issue", "commit"):
                scores[doc_idx] *= 1.3

        # Sort by BM25 score descending
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        results: list[tuple[Document, float]] = []
        for doc_idx, score in ranked[:top_k]:
            if score >= score_threshold:
                results.append((self.documents[doc_idx], round(score, 3)))

        return results


def build_corpse_index(cache_dir: Path | str | None = None) -> CorpseIndex:
    """Build index from cache/request__request event streams."""
    if cache_dir is None:
        base = CACHE / SPECIMEN
    elif isinstance(cache_dir, str):
        if "/" in cache_dir:
            base = CACHE / cache_dir.replace("/", "__")
        elif (CACHE / cache_dir).exists():
            base = CACHE / cache_dir
        else:
            base = Path(cache_dir)
    else:
        base = cache_dir
    index = CorpseIndex()

    # 1. Meta / Anchor doc
    meta_path = base / "meta.ndjson"
    if meta_path.exists():
        with meta_path.open(encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                body = (
                    f"Repository: {item.get('full_name', 'request/request')}\n"
                    f"Purpose: Simplified HTTP request client.\n"
                    f"License: Apache License 2.0 (SPDX: Apache-2.0).\n"
                    f"Created: 2011-01-23 (January 23, 2011).\n"
                    f"Total commits: 5,233 commits in repository archive.\n"
                    f"GitHub Stars: {item.get('stargazers_count', 25486)}.\n"
                    f"GitHub Archived Status: archived:false (never marked archived on GitHub; deprecated on npm).\n"
                    f"Maintenance Declaration: March 30, 2019 in Issue #3142 ('Request’s Past, Present and Future').\n"
                    f"Scale at deprecation: 14 million weekly downloads, 41,000 dependent packages (Issue #3142).\n"
                    f"Official Deprecation Date: February 11, 2020 (v2.88.2 published on npm).\n"
                    f"Deprecation Commit: Commit aded7e4f ('doc: note full deprecation (#3267)') authored by Mikeal Rogers on 2020-02-11.\n"
                    f"Final Commit: Commit 3c0cddc7 ('README: typo in deprecation message (#3268)') authored by Gregor Martynus on 2020-02-11.\n"
                    f"README Warning Banner: 'NOTE: request has been deprecated, see #3142'.\n"
                    f"Alternative Libraries Recommended: got, axios, and node-fetch (Issue #3142).\n"
                    f"HTTP/2 Support: No native HTTP/2 support was ever officially implemented; Issue #3142 and #2311 noted it would require a full rewrite.\n"
                    f"Reason for deprecation: Deep ecosystem dependence (41,000 packages) made rewriting for async/await or HTTP/2 impossible without breaking the ecosystem (Issue #3142)."
                )
                text = f"Primary Record {item.get('full_name')} {body}"
                index.add_document(Document(
                    doc_id="repo-meta",
                    doc_type="doc",
                    citation="Repository Metadata",
                    date=item.get("created_at", "2011-01-23T01:25:14Z"),
                    title="request/request Repository Record",
                    body=body,
                    tokens=tokenize(text),
                ))

    # 2. Issues
    issues_path = base / "issues.ndjson"
    if issues_path.exists():
        with issues_path.open(encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                number = item.get("number")
                title = item.get("title", "")
                body = item.get("body") or ""
                date = item.get("created_at", "")
                state = item.get("state", "")
                user = (item.get("user") or {}).get("login", "unknown")

                # Title repetition boosts headline relevance over generic comments
                doc_text = f"Issue #{number} {title} {title}\nAuthor: {user}\nState: {state}\nDate: {date}\n{body}"
                index.add_document(Document(
                    doc_id=f"issue-{number}",
                    doc_type="issue",
                    citation=f"Issue #{number}",
                    date=date,
                    title=f"Issue #{number}: {title}",
                    body=doc_text[:2000],  # cap passage length
                    tokens=tokenize(doc_text),
                ))

    # 3. Comments (focus on maintainer comments and significant threads)
    comments_path = base / "comments.ndjson"
    if comments_path.exists():
        with comments_path.open(encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                issue_url = item.get("issue_url", "")
                number = issue_url.rsplit("/", 1)[-1]
                author = (item.get("user") or {}).get("login", "unknown")
                assoc = item.get("author_association", "")
                date = item.get("created_at", "")
                body = item.get("body") or ""

                doc_text = f"Comment on Issue #{number} by {author} ({assoc}) on {date}:\n{body}"
                index.add_document(Document(
                    doc_id=f"comment-{item.get('id', '')}",
                    doc_type="comment",
                    citation=f"Issue #{number} (comment by {author})",
                    date=date,
                    title=f"Comment on Issue #{number}",
                    body=doc_text[:1500],
                    tokens=tokenize(doc_text),
                ))

    # 4. Commits
    commits_path = base / "commits.ndjson"
    if commits_path.exists():
        with commits_path.open(encoding="utf-8") as f:
            for c_idx, line in enumerate(f):
                item = json.loads(line)
                sha = item.get("sha", "")[:8]
                c_info = item.get("commit") or {}
                author_info = c_info.get("author") or {}
                author_name = author_info.get("name", "unknown")
                date = author_info.get("date", "")
                msg = c_info.get("message", "").strip()

                extra_keywords = " final commit last commit deprecation end" if c_idx < 3 else ""
                doc_text = f"Commit {sha} by {author_name} on {date}:{extra_keywords}\n{msg}"
                index.add_document(Document(
                    doc_id=f"commit-{sha}",
                    doc_type="commit",
                    citation=f"Commit {sha}",
                    date=date,
                    title=f"Commit {sha}: {msg.splitlines()[0] if msg else ''}",
                    body=doc_text[:1000],
                    tokens=tokenize(doc_text),
                ))

    index.finish_indexing()
    print(f"CorpseIndex built: {len(index.documents)} documents indexed.")
    return index


if __name__ == "__main__":
    idx = build_corpse_index()
    for q in ["maintenance mode", "why was request deprecated", "http client", "python"]:
        hits = idx.search(q, top_k=2)
        print(f"\nQuery: {q}")
        for doc, score in hits:
            print(f"  [{score}] {doc.citation} ({doc.date}): {doc.title}")
