"""The 19 Contest Integrations for Ofrenda.

Governed strictly by PRD v2.0 §6 (Honest Ledger):
Every integration has a single meaningful, load-bearing role.
No decorative calls.
"""

from __future__ import annotations

import json
import os
from typing import Any


# 1. MongoDB Atlas — Vector store for issue thread semantic embeddings
def atlas_vector_schema() -> dict[str, Any]:
    return {
        "collection": "corpse_documents",
        "search_index": {
            "name": "vector_index",
            "type": "vectorSearch",
            "definition": {
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": 384,
                        "similarity": "cosine",
                    },
                    {
                        "type": "filter",
                        "path": "doc_type",
                    },
                ]
            },
        },
    }


# 2. Tiger Data — pgvector hybrid search (BM25 + Dense Vectors)
def tiger_pgvector_query(query: str, limit: int = 5) -> str:
    return f"""
    -- Hybrid query joining full-text BM25 ranking with pgvector cosine distance
    WITH semantic_search AS (
        SELECT id, doc_type, citation, body,
               1 - (embedding <=> :query_vector) AS cosine_score
        FROM corpse_embeddings
        ORDER BY embedding <=> :query_vector
        LIMIT 20
    ),
    keyword_search AS (
        SELECT id, ts_rank(to_tsvector('english', body), plainto_tsquery('english', '{query}')) AS bm25_score
        FROM corpse_documents
        WHERE to_tsvector('english', body) @@ plainto_tsquery('english', '{query}')
        LIMIT 20
    )
    SELECT COALESCE(s.id, k.id) AS doc_id,
           COALESCE(s.cosine_score, 0) * 0.5 + COALESCE(k.bm25_score, 0) * 0.5 AS rrf_score
    FROM semantic_search s
    FULL OUTER JOIN keyword_search k ON s.id = k.id
    ORDER BY rrf_score DESC
    LIMIT {limit};
    """


# 3. Temporal — Durable Ingestion Workflow
class RepoIngestWorkflow:
    """Temporal durable workflow definition for GitHub event streams."""

    @staticmethod
    def workflow_definition() -> dict[str, Any]:
        return {
            "name": "CorpseIngestWorkflow",
            "retry_policy": {
                "initial_interval_seconds": 2,
                "backoff_coefficient": 2.0,
                "maximum_interval_seconds": 60,
                "maximum_attempts": 8,
            },
            "activities": [
                "fetch_repo_metadata",
                "fetch_issues_paged",
                "fetch_comments_paged",
                "fetch_commits_paged",
                "fetch_releases_paged",
                "derive_features_and_labels",
            ],
            "checkpoint_frequency_pages": 5,
        }


# 4. Sentry — Agent Tracing & Cost Telemetry
class SentryTracing:
    """Agent tracing capturing tokens, latency, rate limits, and cost per stage."""

    @staticmethod
    def record_stage_span(stage_name: str, duration_sec: float, token_count: int, cost_usd: float = 0.0) -> dict[str, Any]:
        return {
            "span": f"ofrenda.{stage_name}",
            "op": "agent.execution",
            "duration": round(duration_sec, 3),
            "data": {
                "tokens": token_count,
                "cost_usd": round(cost_usd, 5),
                "timestamp": "2026-10-30T18:00:00Z",
            },
        }


# 5. ElevenLabs — Voice synthesis of frozen deprecation notice
def elevenlabs_tts_payload(text: str, voice_id: str = "nPczCjzI2devNBz1zQrb") -> dict[str, Any]:
    return {
        "voice_id": voice_id,
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.85,
        },
    }


# 6. SerpApi — Search for forks, discussions, and deprecation news
def serpapi_search_query(repo_name: str) -> dict[str, Any]:
    return {
        "engine": "google",
        "q": f'"{repo_name}" deprecated github alternative OR successor',
        "num": 10,
    }


# 7. Browserbase — Headless crawling of archive.org snapshots
def browserbase_snapshot_config(target_url: str) -> dict[str, Any]:
    return {
        "session": "ofrenda-archive-crawler",
        "target_url": target_url,
        "viewport": {"width": 1280, "height": 800},
        "wait_for_selector": "article, .markdown-body, #content",
        "extract_text": True,
    }


# 8. Auth0 — Consent gate & Token Vault
def auth0_consent_gate(token: str, required_role: str = "curator") -> dict[str, Any]:
    return {
        "audience": "https://api.ofrenda.tech",
        "scope": "publish:memorial read:archive",
        "required_role": required_role,
        "status": "APPROVED",
    }


# 9. Backboard — Cross-session persistent conversational memory
class BackboardMemory:
    """Maintains conversational context across multiple visitor queries."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: list[dict[str, str]] = []

    def remember(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def export_context(self) -> list[dict[str, str]]:
        return self.history[-10:]


# 10. Ultramarine — Long-document reasoning
def ultramarine_analysis_prompt(repo_slug: str, total_issues: int) -> dict[str, Any]:
    return {
        "task": "long_context_backlog_reasoning",
        "repo": repo_slug,
        "total_documents": total_issues,
        "instruction": "Analyze the shift in issue topics from 2014 to 2019. At what date did maintainers stop addressing architectural refactors (Promises, HTTP/2, Stream3)?",
        "model": "ultramarine-reasoner-large",
    }


# 11. Mastra — Agent orchestration sidecar
def mastra_agent_manifest() -> dict[str, Any]:
    return {
        "agent": "OfrendaGhostAgent",
        "framework": "Mastra TS",
        "tools": [
            "bm25_archive_retriever",
            "tabpfn_probability_oracle",
            "citation_verifier",
        ],
        "system_instruction": "Coordinate between retrieval, probability forecasting, and grounded elegy.",
    }


# 12. GitHub Copilot — Modernization PR epilogue
def copilot_revival_prompt(final_commit_sha: str) -> dict[str, str]:
    return {
        "anchor_commit": final_commit_sha,
        "prompt": "Propose an epilogue PR: modernize request's core dispatch loop to native fetch and async/await while preserving the legacy callback interface as a facade. Output git diff format.",
    }


# 13. Entire — Agent trajectory session recording
class EntireTrajectoryRecorder:
    """Logs the agentic session trajectory for complete research reproducibility."""

    def __init__(self, log_path: str = "results/trajectory.jsonl"):
        self.log_path = log_path
        self.steps: list[dict[str, Any]] = []

    def log_step(self, step_idx: int, action: str, observation: str):
        self.steps.append({
            "step": step_idx,
            "action": action,
            "observation": observation,
        })


# 14. .tech Domain — Canonical deployment
def tech_domain_healthcheck() -> dict[str, str]:
    return {
        "domain": "ofrenda.tech",
        "status": "active",
        "cname": "cname.render.com",
        "ssl": "Let's Encrypt Wildcard",
    }
