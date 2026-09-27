import pytest

from cosmo.llm import KeyPool, extract_json, is_key_problem, model_kwargs

from fakes import FakeError

MODELS = ["big-model", "small-model"]


def test_key_problems_are_recognised():
    assert is_key_problem(FakeError(429, "Rate limit reached"))
    assert is_key_problem(FakeError(401, "Invalid API Key"))
    assert not is_key_problem(FakeError(404, "model not found"))


def test_needs_at_least_one_key(fake_groq):
    with pytest.raises(ValueError):
        KeyPool(["", None])


def test_switches_to_next_key_when_rate_limited(fake_groq):
    fake_groq.broken_keys = {"k1": (429, "Rate limit"), "k2": (401, "Invalid API Key")}
    pool = KeyPool(["k1", "k2", "k3"])
    meta = {}
    text = "".join(pool.stream_chat([{"role": "user", "content": "hi"}], MODELS, meta))
    assert "Mars" in text
    assert fake_groq.calls == [("k1", "big-model"), ("k2", "big-model"), ("k3", "big-model")]
    assert meta == {"model": "big-model", "ok": True}


def test_remembers_working_key(fake_groq):
    fake_groq.broken_keys = {"k1": (429, "Rate limit")}
    pool = KeyPool(["k1", "k2"])
    "".join(pool.stream_chat([{"role": "user", "content": "hi"}], MODELS))
    fake_groq.calls.clear()
    "".join(pool.stream_chat([{"role": "user", "content": "hi"}], MODELS))
    assert fake_groq.calls == [("k2", "big-model")]


def test_falls_back_to_smaller_model_when_model_retired(fake_groq):
    fake_groq.broken_models = {"big-model"}
    pool = KeyPool(["k1", "k2"])
    meta = {}
    "".join(pool.stream_chat([{"role": "user", "content": "hi"}], MODELS, meta))
    assert meta["model"] == "small-model"
    # a retired model is a model problem: don't waste the other keys on it
    assert fake_groq.calls == [("k1", "big-model"), ("k1", "small-model")]


def test_friendly_message_when_everything_fails(fake_groq):
    fake_groq.broken_keys = {"k1": (429, "Rate limit")}
    pool = KeyPool(["k1"])
    meta = {}
    text = "".join(pool.stream_chat([{"role": "user", "content": "hi"}], MODELS, meta))
    assert "try again" in text.lower()
    assert meta["ok"] is False


def test_transcribe_uses_key_rotation(fake_groq):
    fake_groq.broken_keys = {"k1": (429, "Rate limit")}
    pool = KeyPool(["k1", "k2"])
    assert pool.transcribe(b"audio", ["whisper"]) == "What is Saturn made of?"


def test_gpt_oss_gets_short_reasoning():
    assert model_kwargs("openai/gpt-oss-120b", 600) == {"reasoning_effort": "low", "max_tokens": 1500}
    assert model_kwargs("llama-3.3-70b-versatile", 600) == {"max_tokens": 600}


def test_extract_json_handles_code_fences():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"a": 2} hope it helps') == {"a": 2}
