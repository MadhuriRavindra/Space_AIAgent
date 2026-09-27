import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fakes import FakeBehaviour, FakeGroq  # noqa: E402


@pytest.fixture
def fake_groq(monkeypatch):
    import cosmo.llm
    FakeBehaviour.reset()
    monkeypatch.setattr(cosmo.llm, "Groq", FakeGroq)
    return FakeBehaviour
