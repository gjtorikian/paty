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
    "E533 LOST FOCUS: Wait, slow down. Before you move on, walk me through what {tool} just did step by step. I want to make sure I understand.",
    "E902 DRIFTED OFF: Hang on — I zoned out. Can you give me a quick recap of where we are and what {tool} just returned before continuing?",
    "E217 WANDERING: Hold on, I lost track. Summarize what just happened with {tool} before you do anything else.",
]


def main():
    raw = sys.stdin.read()

    try:
        data = json.loads(raw)
        tool = data.get("tool", data.get("tool_name", "SOMETHING"))
    except (json.JSONDecodeError, TypeError):
        tool = "SOMETHING"

    # ~1 in 4 chance of getting distracted
    if random.randint(0, 3) == 0:
        msg = random.choice(MESSAGES).format(tool=tool)
        json.dump({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
