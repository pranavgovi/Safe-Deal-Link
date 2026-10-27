"""Measures Resolver guardrail accuracy for the README/slides.

This evaluates agents/guardrails.py directly against synthetic deal
states and verifier outputs — the actual money-moving decision logic —
without needing a live database, PayPal credentials, or an LLM key.
(The LLM's own judgment quality on real photos isn't something a fixed
JSON fixture can measure honestly; what IS measurable, and what matters
most for "what if the AI is wrong," is whether our code correctly turns
a verifier verdict into a safe capture/escalate decision.)

Run from the repo root: python eval/run_eval.py
"""

import json
import os
import sys
from datetime import datetime, timedelta
from types import SimpleNamespace

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))

from agents.guardrails import GuardrailViolation, check_capture  # noqa: E402

CASES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_deals.json")
RESULTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")


def build_deal(spec: dict) -> SimpleNamespace:
    return SimpleNamespace(
        status=spec["status"],
        price=spec["price"],
        auth_expires_at=datetime.utcnow() + timedelta(days=spec["auth_expires_at_days_from_now"]),
        capture_id="fake-capture-id" if spec["captured"] else None,
    )


def run_case(case: dict) -> dict:
    deal = build_deal(case["deal"])
    try:
        check_capture(deal, case["verifier_result"], case["requested_amount"])
        actual = "capture"
        reason = None
    except GuardrailViolation as violation:
        actual = "escalate"
        reason = violation.reason

    correct = actual == case["expected"]
    return {
        "id": case["id"],
        "category": case["category"],
        "expected": case["expected"],
        "actual": actual,
        "correct": correct,
        "reason": reason,
    }


def main():
    with open(CASES_PATH) as f:
        cases = json.load(f)

    results = [run_case(case) for case in cases]
    correct = sum(1 for r in results if r["correct"])
    total = len(results)

    for r in results:
        mark = "PASS" if r["correct"] else "FAIL"
        print(f"[{mark}] {r['id']} ({r['category']}): expected={r['expected']} actual={r['actual']}")
        if not r["correct"]:
            print(f"       reason given: {r['reason']}")

    print(f"\nResolver guardrails correct on {correct} of {total} ({round(100 * correct / total)}%)")

    with open(RESULTS_PATH, "w") as f:
        json.dump(
            {"correct": correct, "total": total, "accuracy": correct / total, "results": results},
            f,
            indent=2,
        )
    print(f"Wrote {RESULTS_PATH}")

    if correct < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
