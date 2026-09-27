"""Small text helpers."""
from __future__ import annotations

import re

from .prompts import OFF_TOPIC_REPLY, UNSAFE_REPLY


def clean_name(raw: str) -> str:
    """Keep only a first name made of letters (max 20 chars)."""
    clean = "".join(ch for ch in (raw or "")[:40] if ch.isalpha() or ch in " -'").strip()
    return clean.split(" ")[0][:20].title() if clean else ""


def is_refusal(answer: str) -> bool:
    a = (answer or "").lower()
    return "can't answer this question as i am a space agent" in a or \
        "can’t answer this question as i am a space agent" in a


def is_blocked(answer: str) -> bool:
    return (answer or "").strip() == UNSAFE_REPLY


_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")


def for_speech(text: str) -> str:
    """Remove markdown and emojis so the read-aloud voice sounds natural."""
    t = _EMOJI.sub("", text or "")
    t = re.sub(r"[*_`#>]", "", t)
    t = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", t)
    t = re.sub(r"^\s*[-•]\s*", "", t, flags=re.M)
    return re.sub(r"\s+", " ", t).strip()


def _syllables(word: str) -> int:
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups) - (1 if word.endswith("e") and len(groups) > 1 else 0)
    return max(1, n)


def reading_grade(text: str) -> float:
    """Flesch-Kincaid grade level (approximate). ~4-6 is right for a 9-11 year old."""
    t = for_speech(text)
    sentences = max(1, len(re.findall(r"[.!?]+", t)))
    words = re.findall(r"[A-Za-z']+", t)
    if not words:
        return 0.0
    syl = sum(_syllables(w) for w in words)
    return round(0.39 * len(words) / sentences + 11.8 * syl / len(words) - 15.59, 1)


__all__ = ["clean_name", "is_refusal", "is_blocked", "for_speech", "reading_grade",
           "OFF_TOPIC_REPLY", "UNSAFE_REPLY"]
