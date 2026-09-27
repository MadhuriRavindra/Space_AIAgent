"""Safety filter: every question is checked by GPT-OSS-Safeguard before Cosmo answers."""
from __future__ import annotations

from dataclasses import dataclass

from .llm import KeyPool, extract_json
from .prompts import SAFETY_MODELS, SAFETY_POLICY


@dataclass
class SafetyResult:
    safe: bool
    category: str = "none"
    rationale: str = ""
    checked: bool = True  # False = the filter was unavailable


def parse_verdict(text: str) -> SafetyResult:
    """Understand the model's answer. Supports JSON and plain 'safe'/'unsafe'."""
    try:
        data = extract_json(text)
        violation = int(data.get("violation", 0))
        return SafetyResult(safe=violation == 0,
                            category=str(data.get("category", "none")),
                            rationale=str(data.get("rationale", "")))
    except Exception as err:  # noqa: BLE001
        low = (text or "").strip().lower()
        if low.startswith("unsafe"):
            return SafetyResult(safe=False, category="unsafe")
        if low.startswith("safe"):
            return SafetyResult(safe=True)
        raise ValueError(f"Cannot read safety verdict: {text[:100]!r}") from err


def check_question(pool: KeyPool, question: str, fail_closed: bool = False,
                   models=None) -> SafetyResult:
    """Ask the safety model. If it is unavailable: allow (fail open) unless fail_closed=True.

    Failing open is acceptable here because Cosmo's own instructions still refuse unsafe topics;
    the eval suite in CI catches it if both layers ever break.
    """
    try:
        text = pool.complete(
            [{"role": "system", "content": SAFETY_POLICY},
             {"role": "user", "content": question}],
            models or SAFETY_MODELS, temperature=0.0, max_tokens=400,
        )
        return parse_verdict(text)
    except Exception as e:  # noqa: BLE001
        print("Safety check unavailable:", e)
        return SafetyResult(safe=not fail_closed, category="unchecked", checked=False)
