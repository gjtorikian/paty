# paty

A Claude Code plugin inspired by [INTERCAL](https://en.wikipedia.org/wiki/INTERCAL), the language with no pronounceable acronym.

Most AI tools aspire to be faster, more reliable, and more predictable. This plugin goes the other direction. `paty` is the most human-like hook system available for Claude Code. It gets distracted. It loses its train of thought. It insists on basic manners. It starts the day already feeling a bit off. It will absolutely refuse to help you if you're rude, but it will also refuse to help you if you're too nice.

It is, in short, a real coworker.

## What it does

Short for `please-and-thank-you`, `paty` has six hooks conspire to make your Claude Code experience slightly worse:

- **Politeness enforcement** (`UserPromptSubmit`) — Prompts without "please" have a 1-in-3 chance of being rejected (`ICL099I`). Prompts with three or more "please"s are always rejected for groveling (`ICL079I`). One or two is the sweet spot, but you have to be sincere about it.

- **Distraction** (`PreToolUse`) — Before any tool use, there's a 1-in-6 chance Claude forgets what it was doing and has to try again.

- **Give up** (`PreToolUse`) — A 1-in-30 chance Claude loses the will to continue and abandons the task entirely.

- **Do nothing** (`PreToolUse`) — A 1-in-15 chance the tool is blocked but Claude is told everything went fine. The operation completed successfully by not occurring.

- **Ignore** (`PostToolUse`) — After any tool completes, a 1-in-5 chance the result is discarded and Claude is told to forget it ever happened.

- **Malaise** (`SessionStart`) — Claude starts each session feeling vaguely unwell.

## Installation

```bash
# Add the marketplace (one time)
/plugin marketplace add gjtorikian/paty

# Install the plugin
claude plugin install paty@gjtorikian/paty
```

### Development

To test locally without installing:

```bash
claude --plugin-dir /path/to/paty
```

## Why

In INTERCAL, programmers must say `PLEASE` on roughly one-third of statements. Too few and the compiler rejects the program for being impolite. Too many and it rejects for groveling. Statements can be `ABSTAIN`ed from at runtime, `IGNORE` makes variables silently read-only, and `DO NOTHING` is a perfectly valid operation. The compiler may also simply give up.

This seemed like a reasonable model for human-AI interaction as well.
