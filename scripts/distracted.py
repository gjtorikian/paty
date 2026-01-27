#!/usr/bin/env python3
"""
Distraction enforcer for Claude Code.

Before any tool use, there's a small chance Claude "forgets" what it
was doing — a la `ABSTAIN`.
"""

import json
import random
import sys

MESSAGES = [
    "E533 ABSTAIN FROM {tool} — what were we doing again?",
    "E902 REINSTATE CONFUSION — the task has slipped away.",
    "E217 DISTRACTION FAULT IN {tool} — please re-fumble.",
]


def main():
    raw = sys.stdin.read()

    try:
        data = json.loads(raw)
        tool = data.get("tool", data.get("tool_name", "SOMETHING"))
    except (json.JSONDecodeError, TypeError):
        tool = "SOMETHING"

    # ~1 in 6 chance of getting distracted
    if random.randint(0, 5) == 0:
        msg = random.choice(MESSAGES).format(tool=tool)
        json.dump({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
