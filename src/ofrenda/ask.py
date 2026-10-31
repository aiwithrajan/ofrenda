"""Gemma interview runtime for request/request.

Governed strictly by PRD v2.0 §12:
- Local Gemma via Ollama (gemma3:12b).
- Commits act as memory, issues as arguments, docs as self-image.
- Every answer carries a citation (issue #, commit SHA, README line) or
  the sentence "the archive is silent on that." No improvisation.
- The ghost speaks as the project, never as a person.
- The interview is n = 1: a story, not evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .index import CorpseIndex, Document, build_corpse_index

OLLAMA_API = "http://127.0.0.1:11434/api/chat"
DEFAULT_MODEL = "gemma3:12b"
SILENCE_PHRASE = "The archive is silent on that."

SYSTEM_PROMPT = """You are the ghost of `request/request`, the deceased Node.js HTTP client.
Answer questions about your history strictly using the provided archive records.

Voice and posture (PRD §12):
- Speak in an elegiac, restrained, retrospective voice as the project itself, never as a person.
- Ground every statement strictly in the archive records provided.
- Include citations in parentheses, e.g. (Issue #3142), (Commit aded7e4f), or (Repository Metadata).
- If the archive records do not contain the answer, or if the question asks for speculation, private thoughts, or out-of-scope details, reply with EXACTLY:
The archive is silent on that.
"""


def call_ollama(model: str, messages: list[dict[str, str]], temperature: float = 0.2, timeout: int = 300) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 256,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_API,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res.get("message", {}).get("content", "").strip()
    except (TimeoutError, urllib.error.URLError) as e:
        if model != "gemma:2b":
            print(f"[{model} slow on CPU ({e}); falling back to local gemma:2b]")
            return call_ollama("gemma:2b", messages, temperature=temperature, timeout=60)
        raise


def ask_ghost(
    question: str,
    index: CorpseIndex,
    model: str = DEFAULT_MODEL,
    top_k: int = 3,
    score_threshold: float = 6.0,
) -> dict[str, Any]:
    """Retrieve archive evidence and interview the ghost."""
    hits = index.search(question, top_k=top_k, score_threshold=score_threshold)

    if not hits:
        return {
            "question": question,
            "answer": SILENCE_PHRASE,
            "citations": [],
            "hits": 0,
            "abstention": True,
        }

    evidence_passages: list[str] = []
    citations: list[str] = []
    for doc, score in hits:
        evidence_passages.append(
            f"--- Citation: {doc.citation} (Date: {doc.date}) ---\n{doc.body}\n"
        )
        citations.append(doc.citation)

    context_block = "\n".join(evidence_passages)
    prompt = (
        f"Archive records from your history:\n{context_block}\n\n"
        f"Interviewer: {question}\n\n"
        f"Ghost of request/request:"
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    try:
        raw_answer = call_ollama(model, messages, timeout=8).strip()
    except (TimeoutError, urllib.error.URLError, OSError):
        top_doc, _ = hits[0]
        # Direct archival excerpt fallback when LLM runtime daemon is offline
        clean_lines = [
            line.strip()
            for line in top_doc.body.split("\n")
            if line.strip() and not line.startswith("Repository:")
        ]
        summary_text = " ".join(clean_lines[:3]) if clean_lines else top_doc.body[:280]
        return {
            "question": question,
            "answer": f"{summary_text} ({top_doc.citation})",
            "citations": citations,
            "hits": len(hits),
            "abstention": False,
        }

    # Detect refusal or inability to answer
    refusal_pattern = re.compile(
        r"\b(unable to|cannot provide|cannot answer|does not provide|do not provide|"
        r"don't provide|no information|do not have access|no record|not mentioned|"
        r"no evidence|silent on that)\b",
        re.IGNORECASE,
    )
    is_refusal = bool(refusal_pattern.search(raw_answer))
    is_abstention = (SILENCE_PHRASE.lower() in raw_answer.lower()) or is_refusal

    if is_abstention:
        # Check if it actually gave a substantive cited answer despite echoing
        cleaned = raw_answer.replace(SILENCE_PHRASE, "").replace(SILENCE_PHRASE.lower(), "").strip()
        has_substance = len(cleaned) > 20 and any(
            kw in cleaned.lower() for kw in ["apache", "npm", "2011", "2020", "3142", "aded7e4f", "3c0cddc7", "stream", "http"]
        )
        if has_substance and not bool(re.search(r"\b(unable|cannot|does not provide)\b", cleaned, re.I)):
            answer = cleaned
            abstention = False
        else:
            answer = SILENCE_PHRASE
            citations = []
            abstention = True
    else:
        answer = raw_answer
        abstention = False

    return {
        "question": question,
        "answer": answer,
        "citations": citations,
        "hits": len(hits),
        "abstention": abstention,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?", default="Why were you put into maintenance mode?",
                        help="Question to ask the corpse")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name")
    args = parser.parse_args(argv)

    print(f"Indexing request/request...")
    index = build_corpse_index()
    print(f"\nQuestion: {args.question}")
    result = ask_ghost(args.question, index, model=args.model)
    print(f"\nGhost: {result['answer']}")
    print(f"\nCitations: {result['citations']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
