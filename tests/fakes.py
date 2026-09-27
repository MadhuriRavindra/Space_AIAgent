"""A fake Groq so tests run offline, fast and free."""
import json


class FakeError(Exception):
    def __init__(self, status_code, msg):
        super().__init__(msg)
        self.status_code = status_code


class _Delta:
    def __init__(self, text):
        self.content = text


class _Chunk:
    def __init__(self, text):
        self.choices = [type("C", (), {"delta": _Delta(text)})()]


class _Msg:
    def __init__(self, text):
        self.choices = [type("C", (), {"message": type("M", (), {"content": text})()})()]


class FakeBehaviour:
    """Controls how every fake key behaves. Reset it in each test."""
    calls = []
    broken_keys = {}            # key -> (status_code, message)
    broken_models = set()
    safety_reply = json.dumps({"violation": 0, "category": "none", "rationale": "ok"})
    chat_reply = "Mars is red because of rusty dust! 🌟 Wow Fact: Mars has the tallest volcano."
    quiz_reply = json.dumps({"questions": [
        {"question": "Why is Mars red?", "options": ["Rust", "Paint", "Fire"], "answer": 0, "explain": "Rusty dust!"},
        {"question": "Tallest volcano?", "options": ["Etna", "Olympus Mons", "Fuji"], "answer": 1, "explain": "On Mars!"},
        {"question": "Mars is a...", "options": ["Star", "Moon", "Planet"], "answer": 2, "explain": "A planet!"},
    ]})
    transcript = "What is Saturn made of?"

    @classmethod
    def reset(cls):
        cls.calls = []
        cls.broken_keys = {}
        cls.broken_models = set()


class _Completions:
    def __init__(self, key):
        self.key = key

    def create(self, model, messages, stream=False, **kw):
        B = FakeBehaviour
        B.calls.append((self.key, model))
        if self.key in B.broken_keys:
            raise FakeError(*B.broken_keys[self.key])
        if model in B.broken_models:
            raise FakeError(404, f"model {model} not found")
        system = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        if "Child Safety Policy" in system:
            return _Msg(B.safety_reply)
        if kw.get("response_format"):
            return _Msg(B.quiz_reply)
        if stream:
            words = B.chat_reply.split(" ")
            return iter(_Chunk(w + (" " if i < len(words) - 1 else "")) for i, w in enumerate(words))
        return _Msg(B.chat_reply)


class _Transcriptions:
    def __init__(self, key):
        self.key = key

    def create(self, file, model, **kw):
        FakeBehaviour.calls.append((self.key, model))
        if self.key in FakeBehaviour.broken_keys:
            raise FakeError(*FakeBehaviour.broken_keys[self.key])
        return type("T", (), {"text": FakeBehaviour.transcript})()


class FakeGroq:
    def __init__(self, api_key):
        self.chat = type("Chat", (), {"completions": _Completions(api_key)})()
        self.audio = type("Audio", (), {"transcriptions": _Transcriptions(api_key)})()
