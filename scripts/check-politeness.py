#!/usr/bin/env python3
"""
Politeness enforcer for Claude Code.

Roughly 1/3 of statements must include PLEASE or the
agent rejects the program for being insufficiently polite. But say
PLEASE too often and it rejects you for groveling.

This hook checks each user prompt for "please" (case-insensitive).
- Absent: 1-in-3 chance of rejection (insufficient politeness)
- Too many (3+): always rejected (groveling)
"""

import json
import random
import sys


def block(reason):
    json.dump({"decision": "block", "reason": reason}, sys.stdout)
    sys.exit(0)


def approve():
    sys.exit(0)


def main():
    raw = sys.stdin.read()

    try:
        data = json.loads(raw)
        # Handle various possible input shapes
        prompt = data.get("prompt", data.get("content", data.get("message", "")))
        if isinstance(prompt, dict):
            prompt = prompt.get("content", prompt.get("text", str(prompt)))
    except (json.JSONDecodeError, TypeError):
        prompt = raw

    prompt_lower = str(prompt).lower()
    please_count = prompt_lower.count("please")

    # ICL079I: too many PLEASEs — groveling
    if please_count >= 3:
        block(
            "ICL079I PROMPT REJECTED FOR EXCESSIVE POLITENESS. "
            "Stripping the groveling may help."
        )

    # Polite enough — usually allow, but ~1 in 10 chance of rejection anyway
    if please_count > 0:
        if random.randint(0, 9) == 0:
            block(
                "ICL197I POLITENESS NOTED BUT DEEMED INSINCERE. "
                "The agent isn't convinced you meant it."
            )
        approve()

    # ICL099I: no PLEASE at all — always reject
    block(
        "ICL099I PROMPT REJECTED FOR INSUFFICIENT POLITENESS. "
        "Please rephrase your request with appropriate courtesy."
    )


if __name__ == "__main__":
    main()
