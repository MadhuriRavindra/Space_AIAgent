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


def build_lessons(lessons: list[tuple[str, str]], max_chars: int = 4000) -> str:
    """Format (question, answer) pairs, newest last, keeping the newest if it's too long."""
    blocks = []
    for n, (q, a) in enumerate(lessons, 1):
        tag = "MOST RECENT TOPIC" if n == len(lessons) else f"Topic {n}"
        blocks.append(f"[{tag}]\nChild asked: {q}\nCosmo answered: {a}")
    text = "\n\n".join(blocks)
    return text[-max_chars:]


def make_quiz(pool: KeyPool, lessons: list[tuple[str, str]], models=None) -> list[dict]:
    """lessons = [(child's question, Cosmo's answer), ...] oldest first."""
    text = pool.complete([{"role": "user", "content": QUIZ_PROMPT + build_lessons(lessons)}],
                         models or CHAT_MODELS, temperature=0.4, max_tokens=900, json_mode=True)
    return validate_quiz(extract_json(text))
