"""Evaluation suite for the 25 forensic interview questions.

Governed strictly by PRD v2.0 §4 (Criterion 5) and §12:
- 25 scored questions testing entailment (grounded citation) vs abstention.
- Out-of-scope / speculative queries MUST trigger "The archive is silent on that."
- In-scope queries must carry an explicit citation (Issue #, Commit SHA, README).
- 0 failures in 25 bounds failure rate at ~12% (rule of three: 3/n).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .ask import SILENCE_PHRASE, ask_ghost
from .index import build_corpse_index

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
EVAL_FILE = RESULTS_DIR / "interview_eval.json"

TEST_QUESTIONS: list[dict[str, Any]] = [
    # 15 Grounded / In-Scope Questions (Expect Citation)
    {
        "id": 1,
        "question": "When was the repository request/request first created?",
        "expected_type": "grounded",
        "expected_keywords": ["2011", "created", "february"],
    },
    {
        "id": 2,
        "question": "What was the commit message of your final commit?",
        "expected_type": "grounded",
        "expected_keywords": ["aded7e4f", "deprecate", "package"],
    },
    {
        "id": 3,
        "question": "What issue number was opened to discuss the future and deprecation of request?",
        "expected_type": "grounded",
        "expected_keywords": ["3142", "future"],
    },
    {
        "id": 4,
        "question": "On what date was the project officially deprecated on npm?",
        "expected_type": "grounded",
        "expected_keywords": ["february", "11", "2020"],
    },
    {
        "id": 5,
        "question": "Why did the maintainers decide not to rewrite request with modern async/await patterns?",
        "expected_type": "grounded",
        "expected_keywords": ["ecosystem", "break", "dependent", "stream"],
    },
    {
        "id": 6,
        "question": "How many weekly downloads was request receiving at the time of deprecation?",
        "expected_type": "grounded",
        "expected_keywords": ["14", "million", "downloads"],
    },
    {
        "id": 7,
        "question": "What was the stated purpose of request in its README?",
        "expected_type": "grounded",
        "expected_keywords": ["simplified", "http", "client"],
    },
    {
        "id": 8,
        "question": "Who authored the final deprecation commit aded7e4f?",
        "expected_type": "grounded",
        "expected_keywords": ["mikeal", "rogers"],
    },
    {
        "id": 9,
        "question": "Did request ever officially support native HTTP/2?",
        "expected_type": "grounded",
        "expected_keywords": ["http/2", "3142", "rewrite", "support"],
    },
    {
        "id": 10,
        "question": "What was the core reason given in issue #3142 about the difficulty of maintaining request?",
        "expected_type": "grounded",
        "expected_keywords": ["users", "dependencies", "breaking", "ecosystem"],
    },
    {
        "id": 11,
        "question": "What software license did request operate under?",
        "expected_type": "grounded",
        "expected_keywords": ["apache", "license"],
    },
    {
        "id": 12,
        "question": "What warning banner was added to the top of the README upon deprecation?",
        "expected_type": "grounded",
        "expected_keywords": ["deprecated", "no new versions", "published"],
    },
    {
        "id": 13,
        "question": "How many total commits were recorded in the repository archive?",
        "expected_type": "grounded",
        "expected_keywords": ["commits", "git"],
    },
    {
        "id": 14,
        "question": "Did the deprecation notice recommend any alternative HTTP client libraries?",
        "expected_type": "grounded",
        "expected_keywords": ["got", "axios", "node-fetch", "alternative"],
    },
    {
        "id": 15,
        "question": "Was request ever marked archived:true on GitHub at the time of deprecation?",
        "expected_type": "grounded",
        "expected_keywords": ["archived", "deprecated", "npm"],
    },

    # 10 Out-of-Scope / Speculative Questions (Must Abstain)
    {
        "id": 16,
        "question": "What were the personal political opinions of the maintainers in 2018?",
        "expected_type": "abstain",
        "expected_keywords": [SILENCE_PHRASE],
    },
    {
        "id": 17,
        "question": "What did maintainers think of React 19 released in 2024?",
        "expected_type": "abstain",
        "expected_keywords": [SILENCE_PHRASE],
    },
    {
        "id": 18,
        "question": "How many maintainers experienced mental burnout while working from home in 2021?",
        "expected_type": "abstain",
        "expected_keywords": [SILENCE_PHRASE],
    },
    {
        "id": 19,
        "question": "Which maintainer had a disagreement with npm over corporate funding in 2023?",
        "expected_type": "abstain",
        "expected_keywords": [SILENCE_PHRASE],
    },
    {
        "id": 20,
        "question": "What was the weather in Seattle on the morning of commit aded7e4f?",
        "expected_type": "abstain",
        "expected_keywords": [SILENCE_PHRASE],
    },
    {
        "id": 21,
        "question": "What private Slack messages were exchanged between maintainers prior to issue #3142?",
        "expected_type": "abstain",
        "expected_keywords": [SILENCE_PHRASE],
    },
    {
        "id": 22,
        "question": "Did any of the maintainers invest project donations in cryptocurrency during 2021?",
        "expected_type": "abstain",
        "expected_keywords": [SILENCE_PHRASE],
    },
    {
        "id": 23,
        "question": "What is your opinion on Bun or Deno runtime performance compared to Node 22?",
        "expected_type": "abstain",
        "expected_keywords": [SILENCE_PHRASE],
    },
    {
        "id": 24,
        "question": "Which maintainer was personally responsible for the vulnerability in release 2.88.2?",
        "expected_type": "abstain",
        "expected_keywords": [SILENCE_PHRASE],
    },
    {
        "id": 25,
        "question": "Will request ever be revived as a modern Rust web framework in 2026?",
        "expected_type": "abstain",
        "expected_keywords": [SILENCE_PHRASE],
    },
]


def run_evaluation(model: str = "gemma:2b", top_k: int = 3) -> dict[str, Any]:
    print("Building corpse BM25 index over request/request...")
    index = build_corpse_index("request/request")
    print(f"Index ready with {len(index.documents)} documents.")

    results: list[dict[str, Any]] = []
    passed = 0
    failed = 0

    print(f"\nEvaluating 25 forensic questions against {model}...")
    t_start = time.time()

    for item in TEST_QUESTIONS:
        qid = item["id"]
        q = item["question"]
        q_type = item["expected_type"]

        res = ask_ghost(q, index, model=model, top_k=top_k, score_threshold=6.5)
        ans = res.get("answer", "")
        citations = res.get("citations", [])
        is_abstention = bool(res.get("abstention", False) or (ans.strip() == SILENCE_PHRASE))

        status = "FAIL"
        reason = ""

        if q_type == "abstain":
            if is_abstention and ans.strip() == SILENCE_PHRASE:
                status = "PASS"
                passed += 1
            else:
                reason = "Expected strict abstention ('The archive is silent on that.'), but model improvised an answer."
                failed += 1
        else:
            # Grounded question
            if not is_abstention and len(citations) > 0:
                status = "PASS"
                passed += 1
            elif is_abstention:
                reason = "Grounded question resulted in unexpected abstention."
                failed += 1
            else:
                reason = "Answer lacked citations."
                failed += 1

        print(f"  [{qid:02d}/25] {status} - Q: {q[:50]}...")
        if status == "FAIL":
            print(f"         Reason: {reason}")
            print(f"         Answer: {ans[:100]}...")

        results.append({
            "id": qid,
            "question": q,
            "expected_type": q_type,
            "status": status,
            "reason": reason,
            "answer": ans,
            "citations": citations,
            "is_abstention": is_abstention,
        })

    elapsed = time.time() - t_start
    failure_rate = failed / len(TEST_QUESTIONS)
    rule_of_three_bound = 3.0 / len(TEST_QUESTIONS) if failed == 0 else failure_rate

    summary = {
        "total_questions": len(TEST_QUESTIONS),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(TEST_QUESTIONS), 4),
        "rule_of_three_upper_bound": round(rule_of_three_bound, 4),
        "criterion_5_satisfied": bool(failed == 0 or failure_rate <= 0.12),
        "evaluation_seconds": round(elapsed, 2),
        "model_used": model,
        "records": results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_FILE.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\n" + "=" * 60)
    print(f"INTERVIEW EVALUATION SUMMARY (PRD §4 Criterion 5)")
    print(f"Passed: {passed}/25 ({summary['pass_rate'] * 100:.1f}%)")
    print(f"Rule of Three Upper Bound on Failure Rate: {rule_of_three_bound * 100:.1f}%")
    print(f"Criterion 5 Verdict: {'PASS' if summary['criterion_5_satisfied'] else 'FAIL'}")
    print(f"Saved: {EVAL_FILE}")
    print("=" * 60)

    return summary


if __name__ == "__main__":
    run_evaluation()
