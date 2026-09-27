"""'Quiz me!' questions made from what the child just learned."""
from __future__ import annotations

from .llm import KeyPool, extract_json
from .prompts import CHAT_MODELS, QUIZ_PROMPT


def validate_quiz(data) -> list[dict]:
    """Keep only well-formed questions (3 options, valid answer index)."""
    good = []
    for q in (data or {}).get("questions", []):
        try:
            options = [str(o).strip() for o in q["options"]]
            answer = int(q["answer"])
            if len(options) == 3 and 0 <= answer < 3 and all(options) and str(q["question"]).strip():
                good.append({"question": str(q["question"]).strip(), "options": options,
                             "answer": answer, "explain": str(q.get("explain", "")).strip()})
        except Exception:  # noqa: BLE001
            continue
    return good[:3]


def make_quiz(pool: KeyPool, facts: str, models=None) -> list[dict]:
    text = pool.complete([{"role": "user", "content": QUIZ_PROMPT + facts[-4000:]}],
                         models or CHAT_MODELS, temperature=0.4, max_tokens=900, json_mode=True)
    return validate_quiz(extract_json(text))
