#!/usr/bin/env python3
"""
Voice sincerity analyzer for Claude Code.

Two voice modes, triggered by the prompt text:

  "please listen to me"       → standard voice mode
  "please listen to my haiku" → haiku mode (5-7-5 required)

Both modes record from the microphone via sox, compute a
pseudo-scientific "Paty Vocal Sincerity Index" (PVSI), and
transcribe via macOS Speech framework.

Score must land 35-65:
  < 35 → ICL277I (too desperate)
  > 65 → ICL394I (too composed)

Haiku mode additionally requires the transcription to be a
perfect 5-7-5 haiku at word boundaries.

Transcribed text is checked for politeness (must contain
"please") before being passed through.

Any other prompt approves immediately for text-mode processing.
"""

import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

TRIGGER_HAIKU = "please listen to my haiku"
TRIGGER_VOICE = "please listen to me"

PROFANITY = {
    "fuck", "shit", "damn", "ass", "bitch", "bastard", "crap", "dick",
    "hell", "piss", "cock", "cunt", "bollocks", "bugger", "bloody",
    "wanker", "twat", "arse", "tosser", "sod",
}


def block(reason):
    json.dump({"decision": "block", "reason": reason}, sys.stdout)
    sys.exit(0)


def approve():
    sys.exit(0)


def approve_with_transcription(text):
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "updatedPrompt": text,
            "additionalContext": "VOICE TRANSCRIPTION: " + text,
        }
    }, sys.stdout)
    sys.exit(0)


def record_audio(path, duration=5):
    """Record audio via sox's rec command."""
    if not shutil.which("rec"):
        block(
            "E774 MICROPHONE FAULT — sox is not installed. "
            "Install it with: brew install sox"
        )

    try:
        subprocess.run(
            ["rec", "-q", "-r", "16000", "-c", "1", "-b", "16", path,
             "trim", "0", str(duration)],
            check=True,
            timeout=duration + 10,
            capture_output=True,
        )
    except subprocess.TimeoutExpired:
        block("E774 MICROPHONE FAULT — recording timed out.")
    except subprocess.CalledProcessError as e:
        detail = e.stderr.decode(errors="replace").strip() if e.stderr else "unknown error"
        block(f"E774 MICROPHONE FAULT — {detail}")


def extract_features(path):
    """Run sox stat and parse audio features from stderr."""
    try:
        result = subprocess.run(
            ["sox", path, "-n", "stat"],
            capture_output=True,
            timeout=10,
        )
    except FileNotFoundError:
        block(
            "E774 MICROPHONE FAULT — sox is not installed. "
            "Install it with: brew install sox"
        )
    except subprocess.TimeoutExpired:
        block("E774 MICROPHONE FAULT — audio analysis timed out.")

    # sox stat writes to stderr
    output = result.stderr.decode(errors="replace")
    features = {}
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        try:
            features[key] = float(value)
        except ValueError:
            pass

    return features


def compute_sincerity(features):
    """
    Paty Vocal Sincerity Index (PVSI).

    Four components, each 0-25 points:
      1. Pitch Confidence — rough frequency sweet spot 130-200 Hz
      2. Dynamic Commitment — RMS amplitude sweet spot 0.02-0.08
      3. Tonal Stability — RMS delta / RMS ratio sweet spot 0.3-0.7
      4. Conviction Quotient — max amplitude / mean norm sweet spot 3-8
    """

    def score_component(value, low_extreme, low_sweet, high_sweet, high_extreme):
        """Piecewise linear scoring: 0 at extremes, 12 at sweet edges, 25 in sweet spot."""
        if value is None:
            return 12.5  # missing data gets middle score
        if low_sweet <= value <= high_sweet:
            mid = (low_sweet + high_sweet) / 2
            half_range = (high_sweet - low_sweet) / 2
            if half_range == 0:
                return 25.0
            dist = abs(value - mid) / half_range
            return 25.0 - (13.0 * dist)
        elif low_extreme <= value < low_sweet:
            span = low_sweet - low_extreme
            if span == 0:
                return 0.0
            return 12.0 * (value - low_extreme) / span
        elif high_sweet < value <= high_extreme:
            span = high_extreme - high_sweet
            if span == 0:
                return 0.0
            return 12.0 * (1.0 - (value - high_sweet) / span)
        else:
            return 0.0

    freq = features.get("rough frequency")
    pitch = score_component(freq, 50, 130, 200, 350)

    rms = features.get("rms amplitude")
    dynamic = score_component(rms, 0.0, 0.02, 0.08, 0.2)

    rms_delta = features.get("rms delta")
    rms_val = features.get("rms amplitude")
    if rms_delta is not None and rms_val and rms_val > 0:
        stability_ratio = abs(rms_delta) / rms_val
    else:
        stability_ratio = None
    stability = score_component(stability_ratio, 0.0, 0.3, 0.7, 1.5)

    max_amp = features.get("maximum amplitude")
    mean_norm = features.get("mean norm")
    if max_amp is not None and mean_norm and mean_norm > 0:
        conviction_ratio = max_amp / mean_norm
    else:
        conviction_ratio = None
    conviction = score_component(conviction_ratio, 0.0, 3.0, 8.0, 20.0)

    return round(pitch + dynamic + stability + conviction)


def count_syllables(word):
    """Count syllables in a word using vowel-group heuristic."""
    word = word.lower().strip()
    word = re.sub(r"[^a-z]", "", word)
    if not word:
        return 0
    if len(word) <= 2:
        return 1

    # Count vowel groups
    count = len(re.findall(r"[aeiouy]+", word))

    # Silent e at end (e.g. "code", "make") but not "le" endings ("apple")
    if word.endswith("e") and not word.endswith("le") and count > 1:
        count -= 1
    # -ed ending is usually silent unless preceded by t/d
    if word.endswith("ed") and len(word) > 3 and word[-3] not in "td":
        count -= 1

    return max(count, 1)


def check_haiku(text):
    """
    Validate that text forms a 5-7-5 haiku at word boundaries.

    Returns (is_valid, line_syllables, words_per_line) or blocks with
    ICL575I if the structure is wrong.
    """
    words = text.split()
    syllables = [count_syllables(w) for w in words]
    target = [5, 7, 5]

    # Try to split words into three groups matching 5-7-5
    def find_split(word_syls, targets, idx=0):
        if not targets:
            return idx == len(word_syls)
        goal = targets[0]
        total = 0
        for i in range(idx, len(word_syls)):
            total += word_syls[i]
            if total == goal:
                if find_split(word_syls, targets[1:], i + 1):
                    return True
            if total > goal:
                break
        return False

    total = sum(syllables)
    valid = total == 17 and find_split(syllables, target)

    if not valid:
        # Build a diagnostic showing what we counted
        word_detail = ", ".join(f"{w}({s})" for w, s in zip(words, syllables))
        block(
            f"ICL575I HAIKU REJECTED — expected 5-7-5 (17 syllables), "
            f"got {total}. Word counts: {word_detail}"
        )


def get_transcriber():
    """Build the bundled Swift transcriber if needed, return path to binary."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    swift_src = os.path.join(script_dir, "transcribe.swift")
    binary = os.path.join(script_dir, "transcribe")

    if os.path.exists(binary) and os.path.getmtime(binary) >= os.path.getmtime(swift_src):
        return binary

    if not shutil.which("swiftc"):
        block(
            "E891 TRANSCRIPTION FAULT — swiftc not found. "
            "Install Xcode Command Line Tools: xcode-select --install"
        )

    try:
        subprocess.run(
            ["swiftc", "-o", binary, swift_src],
            check=True,
            capture_output=True,
            timeout=60,
        )
    except subprocess.CalledProcessError as e:
        detail = e.stderr.decode(errors="replace").strip() if e.stderr else "build failed"
        block(f"E891 TRANSCRIPTION FAULT — {detail}")
    except subprocess.TimeoutExpired:
        block("E891 TRANSCRIPTION FAULT — transcriber build timed out.")

    return binary


def transcribe(path):
    """Transcribe audio via bundled Swift helper (Apple Speech framework)."""
    binary = get_transcriber()

    try:
        result = subprocess.run(
            [binary, path],
            capture_output=True,
            timeout=30,
            text=True,
        )
    except subprocess.TimeoutExpired:
        block("E891 TRANSCRIPTION FAULT — transcription timed out.")

    if result.returncode != 0:
        detail = result.stderr.strip() if result.stderr else "unknown error"
        if detail.startswith("error: "):
            detail = detail[7:]
        block(f"E891 TRANSCRIPTION FAULT — {detail}")

    text = result.stdout.strip()
    if not text:
        block("E891 TRANSCRIPTION FAULT — silence detected, no speech recognized.")

    return text


def check_profanity(text):
    """Block if text contains profanity."""
    words = set(re.findall(r"[a-z]+", text.lower()))
    found = words & PROFANITY
    if found:
        block(
            "ICL666I TRANSCRIPTION REJECTED FOR CONDUCT UNBECOMING. "
            "This is a professional environment."
        )


def check_politeness(text):
    """Apply politeness rules to text. Blocks if impolite."""
    please_count = text.lower().count("please")
    if please_count >= 3:
        block(
            "ICL079I TRANSCRIPTION REJECTED FOR EXCESSIVE POLITENESS. "
            "Stripping the groveling may help."
        )
    if please_count == 0:
        block(
            "ICL099I TRANSCRIPTION REJECTED FOR INSUFFICIENT POLITENESS. "
            "Please rephrase your request with appropriate courtesy."
        )
    if random.randint(0, 9) == 0:
        block(
            "ICL197I POLITENESS NOTED BUT DEEMED INSINCERE. "
            "The agent isn't convinced you meant it."
        )


def voice_pipeline(wav_path, haiku_mode=False):
    """Shared recording → scoring → transcription → validation pipeline."""
    duration = 10 if haiku_mode else 7
    mode_label = "HAIKU" if haiku_mode else "VOICE"
    print(f"\U0001F3A4 SPEAK NOW ({mode_label} MODE) — you have {duration} seconds...",
          file=sys.stderr, flush=True)
    record_audio(wav_path, duration=duration)
    print("\U0001F50A Analyzing vocal sincerity...", file=sys.stderr, flush=True)

    features = extract_features(wav_path)
    score = compute_sincerity(features)

    if score < 35:
        block(
            f"ICL277I VOCAL SINCERITY SCORE {score}/100 — "
            "REJECTED FOR EXCESSIVE DESPERATION."
        )

    if score > 65:
        block(
            f"ICL394I VOCAL SINCERITY SCORE {score}/100 — "
            "REJECTED FOR SUSPICIOUS COMPOSURE."
        )

    print(f"\u2705 VOCAL SINCERITY SCORE {score}/100 — ACCEPTED.",
          file=sys.stderr, flush=True)

    text = transcribe(wav_path)

    if haiku_mode:
        check_haiku(text)
        print("\U0001F338 HAIKU STRUCTURE VALID (5-7-5).",
              file=sys.stderr, flush=True)

    check_profanity(text)
    check_politeness(text)

    return text


def main():
    raw = sys.stdin.read()

    try:
        data = json.loads(raw)
        prompt = data.get("prompt", data.get("content", data.get("message", "")))
        if isinstance(prompt, dict):
            prompt = prompt.get("content", prompt.get("text", str(prompt)))
    except (json.JSONDecodeError, TypeError):
        prompt = raw

    prompt_lower = str(prompt).lower()

    # Check triggers (haiku first since it's a longer prefix)
    haiku_mode = prompt_lower.startswith(TRIGGER_HAIKU)
    voice_mode = haiku_mode or prompt_lower.startswith(TRIGGER_VOICE)

    if not voice_mode:
        approve()

    tmp = tempfile.NamedTemporaryFile(
        prefix="paty_voice_", suffix=".wav", delete=False
    )
    tmp.close()
    wav_path = tmp.name

    try:
        text = voice_pipeline(wav_path, haiku_mode=haiku_mode)
        approve_with_transcription(text)
    finally:
        try:
            os.unlink(wav_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
