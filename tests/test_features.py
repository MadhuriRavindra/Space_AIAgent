import pytest

from cosmo import nasa
from cosmo.llm import KeyPool
from cosmo.prompts import OFF_TOPIC_REPLY
from cosmo.quiz import build_lessons, make_quiz, validate_quiz
from cosmo.ranks import rank_for
from cosmo.text import clean_name, for_speech, is_chitchat, is_refusal, reading_grade


# ---- NASA pictures ----
@pytest.mark.parametrize("question,expected", [
    ("Why does Saturn have rings?", "Saturn rings Cassini"),
    ("what is a black hole", "black hole event horizon"),
    ("How do astronauts sleep on the ISS?", "International Space Station orbit"),
    ("Tell me about the Sun!", "Sun solar dynamics observatory"),
    ("What are stars made of?", "star cluster Hubble"),
    ("what did you do on sunday", None),        # 'sunday' is not 'sun'
    ("who is the best cricket player", None),
])
def test_image_query(question, expected):
    assert nasa.image_query_for(question) == expected


def test_parse_nasa_search_response():
    data = {"collection": {"items": [{
        "data": [{"title": "Saturn Atmosphere", "nasa_id": "PIA01973", "media_type": "image"}],
        "links": [{"href": "https://images-assets.nasa.gov/image/PIA01973/PIA01973~thumb.jpg", "render": "image"}],
    }]}}
    img = nasa.parse_search(data)
    assert img["title"] == "Saturn Atmosphere" and img["url"].endswith("~thumb.jpg")
    assert nasa.parse_search({"collection": {"items": []}}) is None


# ---- Quiz ----
def test_quiz_from_fake_model(fake_groq):
    quiz = make_quiz(KeyPool(["k1"]), [("Why is Mars red?", "Mars is red because of rust.")])
    assert len(quiz) == 3 and quiz[0]["options"][quiz[0]["answer"]] == "Rust"


def test_lessons_mark_most_recent_topic_and_keep_it_when_long():
    text = build_lessons([("Saturn?", "Rings of ice."), ("Mars?", "Red rust.")])
    assert text.index("[Topic 1]") < text.index("[MOST RECENT TOPIC]")
    assert "Child asked: Mars?" in text.split("[MOST RECENT TOPIC]")[1]
    long_text = build_lessons([("Old?", "x" * 5000), ("New?", "Newest fact.")], max_chars=300)
    assert "Newest fact." in long_text and len(long_text) <= 300


def test_bad_quiz_questions_are_dropped():
    data = {"questions": [
        {"question": "ok?", "options": ["a", "b", "c"], "answer": 1},
        {"question": "two options", "options": ["a", "b"], "answer": 0},
        {"question": "bad index", "options": ["a", "b", "c"], "answer": 5},
        {"question": "", "options": ["a", "b", "c"], "answer": 0},
    ]}
    assert [q["question"] for q in validate_quiz(data)] == ["ok?"]


# ---- Ranks ----
def test_ranks():
    assert rank_for(0)["name"] == "Space Cadet"
    assert rank_for(5)["name"] == "Rocket Pilot"
    assert rank_for(8)["progress"] == pytest.approx(3 / 7, abs=0.01)
    top = rank_for(99)
    assert top["name"] == "Astronaut" and top["next_name"] is None and top["progress"] == 1.0


# ---- Text helpers ----
@pytest.mark.parametrize("raw,expected", [
    ("tanvi", "Tanvi"), ("  aarav sharma ", "Aarav"), ("<script>", "Script"), ("123", ""), ("", ""),
])
def test_clean_name(raw, expected):
    assert clean_name(raw) == expected


def test_refusal_detection():
    assert is_refusal(OFF_TOPIC_REPLY)
    assert not is_refusal("Mars is a planet!")


def test_speech_text_has_no_markdown_or_emoji():
    assert for_speech("**Mars** is red 🔴!\n- cool") == "Mars is red ! cool"


def test_reading_grade_is_lower_for_simple_text():
    simple = "The Sun is a big ball of hot gas. It gives us light. It keeps us warm."
    hard = ("Heliophysical magnetohydrodynamic phenomena substantially complicate "
            "comprehensive characterisation of stellar atmospheric stratification.")
    assert reading_grade(simple) < 5 < reading_grade(hard)


@pytest.mark.parametrize("text,chitchat", [
    ("hi", True), ("Hello Cosmo!", True), ("thank you", True), ("wow cool", True),
    ("Which planet is hottest?", False),   # 'which' contains 'hi' but is a real question
    ("What is Pluto?", False), ("ok tell me about the moon", False), ("", False),
])
def test_chitchat(text, chitchat):
    assert is_chitchat(text) is chitchat
