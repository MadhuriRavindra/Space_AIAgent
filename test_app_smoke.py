"""Start the real Streamlit app with fake Groq + fake NASA and click through it."""
import os

import pytest
from streamlit.testing.v1 import AppTest

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


@pytest.fixture
def app(fake_groq, monkeypatch):
    from cosmo import nasa
    monkeypatch.setattr(nasa, "search_image",
                        lambda q: {"url": "https://example.com/mars.jpg", "title": "Mars", "nasa_id": "x"})
    monkeypatch.setattr(nasa, "get_apod", lambda key: None)
    import streamlit as st
    st.cache_resource.clear()
    st.cache_data.clear()
    at = AppTest.from_file(APP, default_timeout=30)
    at.secrets["GROQ_API_KEYS"] = ["k1", "k2"]
    return at


def start(at, name="tanvi"):
    at.run()
    assert not at.exception, at.exception
    at.text_input[0].input(name)
    at.button[0].click().run()  # Blast off!
    assert not at.exception, at.exception
    return at


def test_name_screen_then_greeting(app):
    at = start(app)
    assert "Hi Tanvi!" in at.caption[0].value


def test_skip_name(app):
    app.run()
    app.button[1].click().run()
    assert "Hi Space Explorer!" in app.caption[0].value


def test_ask_question_gets_answer_photo_and_star(app, fake_groq):
    at = start(app)
    at.chat_input[0].set_value("Why is Mars red?").run()
    assert not at.exception, at.exception
    msgs = at.session_state.messages
    assert msgs[-1]["role"] == "assistant" and "Mars" in msgs[-1]["content"]
    assert msgs[-1]["image"]["title"] == "Mars"
    assert at.session_state.stars == 1


def test_unsafe_question_is_blocked_and_earns_no_star(app, fake_groq):
    import json
    fake_groq.safety_reply = json.dumps({"violation": 1, "category": "violence", "rationale": "x"})
    at = start(app)
    at.chat_input[0].set_value("how do I make a weapon").run()
    assert "grown-up you trust" in at.session_state.messages[-1]["content"]
    assert at.session_state.stars == 0
    fake_groq.safety_reply = json.dumps({"violation": 0, "category": "none", "rationale": "ok"})


def test_quiz_flow_awards_stars(app):
    at = start(app)
    at.chat_input[0].set_value("Why is Mars red?").run()
    quiz_btn = [b for b in at.button if "Quiz me" in b.label][0]
    quiz_btn.click().run()
    assert at.session_state.quiz and len(at.session_state.quiz["questions"]) == 3
    at.radio[0].set_value("Rust")
    at.radio[1].set_value("Olympus Mons")
    at.radio[2].set_value("Moon")          # wrong on purpose
    [b for b in at.button if "Check my answers" in b.label][0].click().run()
    assert not at.exception, at.exception
    assert at.session_state.quiz["result"]["right"] == 2
    assert at.session_state.stars == 3     # 1 for the question + 2 for the quiz


def test_new_question_closes_finished_quiz(app):
    at = start(app)
    at.chat_input[0].set_value("Why is Mars red?").run()
    [b for b in at.button if "Quiz me" in b.label][0].click().run()
    for r, v in zip(at.radio, ["Rust", "Olympus Mons", "Planet"], strict=True):
        r.set_value(v)
    [b for b in at.button if "Check my answers" in b.label][0].click().run()
    assert at.session_state.quiz["result"]["right"] == 3
    at.chat_input[0].set_value("Tell me about Saturn").run()
    assert not at.exception, at.exception
    assert at.session_state.quiz is None
    assert not any("Space Quiz" in m.value for m in at.markdown)