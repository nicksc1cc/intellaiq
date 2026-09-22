#!/usr/bin/env python3
"""StickyRice TypeSafe JEV adapter.

Uses TypeSafe Python SDK to run Jev judgments via TypeSafe API.
"""
import os
import json
import sys
from typing import Any, Dict

try:
    from typesafe_sdk import TypeSafeClient, Choice, Noul, Score
except ImportError:
    print(json.dumps({"error": "typesafe-sdk not installed. Run: pip install typesafe-sdk"}), file=sys.stderr)
    sys.exit(1)


def build_questions(request_questions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Convert StickyRice question format to TypeSafe SDK question objects."""
    questions = {}
    for qid, qdef in request_questions.items():
        qtype = qdef.get("type", "").lower()
        instructions = qdef.get("instructions", "")
        criteria = qdef.get("criteria")

        if qtype == "noul":
            questions[qid] = Noul(
                instructions=instructions,
            )
        elif qtype == "choice":
            if not isinstance(criteria, dict):
                raise ValueError(f"Choice question {qid} requires 'criteria' as dict")
            questions[qid] = Choice(
                instructions=instructions,
                criteria=criteria,
            )
        elif qtype == "score":
            if not isinstance(criteria, list):
                raise ValueError(f"Score question {qid} requires 'criteria' as list")
            questions[qid] = Score(
                instructions=instructions,
                criteria=criteria,
            )
        else:
            raise ValueError(f"Unknown question type: {qtype}")
    return questions


def main():
    # Read request from stdin
    try:
        request = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}), file=sys.stderr)
        sys.exit(1)

    # Required fields
    if "state" not in request or "questions" not in request:
        print(json.dumps({"error": "Request must contain 'state' and 'questions'"}), file=sys.stderr)
        sys.exit(1)

    # Get API key from environment
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        print(json.dumps({"error": "TYPESAFE_API_KEY not set in environment"}), file=sys.stderr)
        sys.exit(1)

    # Build questions
    try:
        questions = build_questions(request["questions"])
    except ValueError as e:
        print(json.dumps({"error": f"Invalid question format: {e}"}), file=sys.stderr)
        sys.exit(1)

    # Create client
    client = TypeSafeClient(api_key=api_key)

    # Run questions
    state = request["state"]
    if isinstance(state, dict):
        state = json.dumps(state)

    try:
        result = client.system_one(state, questions)
    except Exception as e:
        print(json.dumps({"error": f"TypeSafe API error: {e}"}), file=sys.stderr)
        sys.exit(1)

    # Add StickyRice metadata
    result_dict = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    result_dict["sticky_rice"] = {
        "engine": "typesafe-jev",
        "question_count": len(request["questions"]),
    }

    # Output result
    print(json.dumps(result_dict, indent=2, default=str))


if __name__ == "__main__":
    main()