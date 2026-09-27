"""The full answer pipeline, shared by the app and the eval suite so we test exactly what runs live.

question -> safety check -> Cosmo answers (streamed) -> [app adds NASA photo]
"""
from __future__ import annotations

from .llm import KeyPool
from .prompts import CHAT_MODELS, UNSAFE_REPLY, build_system_prompt
from .safety import SafetyResult, check_question

HISTORY_TURNS = 10


def build_messages(history: list[dict], name: str) -> list[dict]:
    chat = [{"role": m["role"], "content": m["content"]} for m in history if m.get("role") in ("user", "assistant")]
    return [{"role": "system", "content": build_system_prompt(name)}] + chat[-HISTORY_TURNS:]


def respond(pool: KeyPool, history: list[dict], name: str = "", meta: dict | None = None,
            fail_closed: bool = False, chat_models=None):
    """Yield the answer piece by piece. meta gets: safety, model, ok."""
    meta = meta if meta is not None else {}
    question = history[-1]["content"]
    verdict: SafetyResult = check_question(pool, question, fail_closed=fail_closed)
    meta["safety"] = verdict
    if not verdict.safe:
        meta.update(model=None, ok=True, blocked=True)
        yield UNSAFE_REPLY
        return
    meta["blocked"] = False
    yield from pool.stream_chat(build_messages(history, name), chat_models or CHAT_MODELS, meta)


def respond_text(pool: KeyPool, question: str, name: str = "", meta: dict | None = None, **kw) -> str:
    return "".join(respond(pool, [{"role": "user", "content": question}], name, meta, **kw))
