"""Groq access: several API keys with automatic switching, plus model fallback."""
from __future__ import annotations

import json
import re

from groq import Groq


def is_key_problem(err: Exception) -> bool:
    """True when another key could help (rate limit, quota, bad or expired key)."""
    status = getattr(err, "status_code", None)
    text = str(err).lower()
    return status in (401, 403, 429) or any(
        s in text for s in ("rate limit", "invalid api key", "quota", "expired")
    )


def model_kwargs(model: str, max_tokens: int) -> dict:
    """GPT-OSS models think before answering: keep thinking short and leave room for the answer."""
    if "gpt-oss" in model:
        return {"reasoning_effort": "low", "max_tokens": max(max_tokens, 1500)}
    return {"max_tokens": max_tokens}


class KeyPool:
    """One Groq client per key. Remembers which key worked last, shared by all visitors."""

    def __init__(self, keys: list[str]):
        keys = list(dict.fromkeys(k for k in keys if k))
        if not keys:
            raise ValueError("No Groq API key given")
        self.clients = [Groq(api_key=k) for k in keys]
        self.current = 0

    def _order(self):
        n = len(self.clients)
        return [(self.current + i) % n for i in range(n)]

    def run(self, models: list[str], call):
        """Try call(client, model) with every key per model; return the first result.

        Key problems -> next key, same model. Other errors (e.g. model retired) -> next model.
        """
        last_error = None
        for model in models:
            for idx in self._order():
                try:
                    result = call(self.clients[idx], model)
                    self.current = idx
                    return result, model
                except Exception as e:  # noqa: BLE001
                    last_error = e
                    print(f"Groq key #{idx + 1} / {model} failed: {type(e).__name__}: {e}")
                    if not is_key_problem(e):
                        break
        raise RuntimeError(f"All Groq keys/models failed: {last_error}")

    # ---- chat ----
    def stream_chat(self, messages, models, meta: dict | None = None, temperature=0.6, max_tokens=600):
        """Yield text pieces. Falls back across keys/models until the first piece arrives."""
        meta = meta if meta is not None else {}
        last_error = None
        for model in models:
            for idx in self._order():
                started = False
                try:
                    stream = self.clients[idx].chat.completions.create(
                        model=model, messages=messages, temperature=temperature,
                        stream=True, **model_kwargs(model, max_tokens),
                    )
                    for chunk in stream:
                        piece = chunk.choices[0].delta.content or ""
                        if piece:
                            started = True
                        yield piece
                    self.current = idx
                    meta.update(model=model, ok=True)
                    return
                except Exception as e:  # noqa: BLE001
                    last_error = e
                    print(f"Groq key #{idx + 1} / {model} failed: {type(e).__name__}: {e}")
                    if started:
                        meta.update(model=model, ok=False)
                        yield "\n\n😕 Oops, Cosmo's radio cut out. Please ask again!"
                        return
                    if not is_key_problem(e):
                        break
        print("All Groq keys/models failed:", last_error)
        meta.update(model=None, ok=False)
        yield "😕 Cosmo's radio is fuzzy right now. Please try again in a minute!"

    def complete(self, messages, models, temperature=0.3, max_tokens=800, json_mode=False) -> str:
        def call(client, model):
            kwargs = dict(model=model, messages=messages, temperature=temperature,
                          **model_kwargs(model, max_tokens))
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            return client.chat.completions.create(**kwargs).choices[0].message.content or ""
        text, _ = self.run(models, call)
        return text

    # ---- speech to text ----
    def transcribe(self, audio_bytes: bytes, models, filename="question.wav") -> str:
        def call(client, model):
            r = client.audio.transcriptions.create(
                file=(filename, audio_bytes), model=model, language="en", temperature=0.0,
            )
            return (getattr(r, "text", None) or "").strip()
        text, _ = self.run(models, call)
        return text


def extract_json(text: str):
    """Parse JSON even if the model wrapped it in ```json fences or extra words."""
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:  # noqa: BLE001
        pass
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        return json.loads(m.group(0))
    raise ValueError("No JSON found")
