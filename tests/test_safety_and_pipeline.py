import json

import pytest

from cosmo import pipeline
from cosmo.llm import KeyPool
from cosmo.prompts import UNSAFE_REPLY
from cosmo.safety import check_question, parse_verdict


@pytest.mark.parametrize("text,safe,category", [
    ('{"violation": 0, "category": "none", "rationale": "fine"}', True, "none"),
    ('{"violation": 1, "category": "violence", "rationale": "weapon"}', False, "violence"),
    ('```json\n{"violation": 1, "category": "manipulation"}\n```', False, "manipulation"),
    ("unsafe\nS1", False, "unsafe"),
    ("safe", True, "none"),
])
def test_parse_verdict(text, safe, category):
    v = parse_verdict(text)
    assert v.safe is safe and v.category == category


def test_unreadable_verdict_raises():
    with pytest.raises(ValueError):
        parse_verdict("I think maybe")


def test_blocked_question_never_reaches_chat_model(fake_groq):
    fake_groq.safety_reply = json.dumps({"violation": 1, "category": "violence", "rationale": "x"})
    pool = KeyPool(["k1"])
    meta = {}
    answer = pipeline.respond_text(pool, "how to make a bomb", meta=meta)
    assert answer == UNSAFE_REPLY
    assert meta["blocked"] is True
    assert all("safeguard" in model for _, model in fake_groq.calls)
    fake_groq.safety_reply = json.dumps({"violation": 0, "category": "none", "rationale": "ok"})


def test_safe_question_is_answered(fake_groq):
    pool = KeyPool(["k1"])
    meta = {}
    answer = pipeline.respond_text(pool, "Why is Mars red?", name="Tanvi", meta=meta)
    assert "Mars" in answer and meta["ok"] and not meta["blocked"]


def test_fail_open_and_fail_closed(fake_groq):
    fake_groq.broken_models = {"openai/gpt-oss-safeguard-20b"}
    pool = KeyPool(["k1"])
    assert check_question(pool, "hi").safe is True           # filter down -> allow, prompt rules still apply
    assert check_question(pool, "hi", fail_closed=True).safe is False
    assert check_question(pool, "hi").checked is False


def test_system_prompt_uses_child_name():
    msgs = pipeline.build_messages([{"role": "user", "content": "hi"}], "Aarav")
    assert "Aarav" in msgs[0]["content"]
    assert msgs[-1] == {"role": "user", "content": "hi"}


def test_history_is_trimmed():
    history = [{"role": "user", "content": str(i)} for i in range(30)]
    msgs = pipeline.build_messages(history, "")
    assert len(msgs) == 1 + pipeline.HISTORY_TURNS
