# paty

A Claude Code plugin inspired by [INTERCAL](https://en.wikipedia.org/wiki/INTERCAL), the language with no pronounceable acronym.

Most AI tools aspire to be faster, more reliable, and more predictable. This plugin goes the other direction. `paty` is the most human-like hook system available for Claude Code. It gets distracted. It loses its train of thought. It insists on basic manners. It starts the day already feeling a bit off. It will absolutely refuse to help you if you're rude, but it will also refuse to help you if you're too nice.

It is, in short, a real coworker.

## What it does

Short for `please-and-thank-you`, `paty` has seven hooks conspire to make your Claude Code experience slightly worse:

- **Voice sincerity** (`UserPromptSubmit`) — Start your prompt with "please listen to me" to activate voice mode. Records from your microphone (with a macOS notification countdown), analyzes pseudo-scientific vocal metrics for a sincerity score (0-100). Score must land 40-60: below is rejected for excessive desperation (`ICL277I`), above for suspicious composure (`ICL394I`). Passing audio is transcribed and fed through the politeness check. Haiku mode: start with "please listen to my haiku" — same sincerity check, plus the transcription must be a perfect 5-7-5 (`ICL575I`). Any other prompt is processed as text.

- **Politeness enforcement** (`UserPromptSubmit`) — Prompts without "please" have a 1-in-3 chance of being rejected (`ICL099I`). Prompts with three or more "please"s are always rejected for groveling (`ICL079I`). One or two is the sweet spot, but you have to be sincere about it.

- **Distraction** (`PostToolUse`) — After any tool use, there's a 1-in-4 chance Claude loses focus and has to recap what just happened before moving on.

- **Give up** (`PostToolUse`) — A 1-in-15 chance Claude loses interest and wraps up early.

- **Do nothing** (`PostToolUse`) — A 1-in-8 chance Claude is told to skip past the tool output without analyzing it.

- **Ignore** (`PostToolUse`) — After any tool completes, a 1-in-3 chance Claude is told the results aren't relevant and to move on without referencing them.

- **Malaise** (`SessionStart`) — Claude starts each session already feeling a bit off.

## Installation

```bash
# Add the marketplace (one time)
/plugin marketplace add gjtorikian/paty

# Install the plugin
claude plugin install paty@gjtorikian/paty
```

### Optional: Voice sincerity dependency

Voice sincerity requires `sox` for audio recording/analysis:

```bash
brew install sox
```

Transcription uses the macOS Speech framework via a bundled Swift helper (auto-compiled on first run — requires Xcode Command Line Tools). Start any prompt with "please listen to me" to activate voice mode.

### Development

To test locally without installing:

```bash
claude --plugin-dir /path/to/paty
```

## Why

In INTERCAL, programmers must say `PLEASE` on roughly one-third of statements. Too few and the compiler rejects the program for being impolite. Too many and it rejects for groveling. Statements can be `ABSTAIN`ed from at runtime, `IGNORE` makes variables silently read-only, and `DO NOTHING` is a perfectly valid operation. The compiler may also simply give up.

This seemed like a reasonable model for human-AI interaction as well.
