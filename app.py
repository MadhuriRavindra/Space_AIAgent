"""
🚀 Space Explorer: a kid-friendly space Q&A app
Streamlit UI + Groq (chat, speech-to-text, safety filter) + NASA pictures
"""
import hashlib
import json
import random

import streamlit as st
import streamlit.components.v1 as components

from cosmo import __version__, nasa, pipeline
from cosmo.llm import KeyPool
from cosmo.prompts import APOD_PROMPT, CHAT_MODELS, WHISPER_MODELS
from cosmo.quiz import make_quiz
from cosmo.ranks import rank_for
from cosmo.text import clean_name, for_speech, is_blocked, is_chitchat, is_refusal

MAX_QUESTION_CHARS = 300      # keeps questions short
MAX_QUESTIONS_PER_VISIT = 40  # protects the free Groq quota when many kids use it


# ---------- Settings (Streamlit secrets) ----------
def secret(key, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def groq_keys():
    keys = secret("GROQ_API_KEYS") or []
    if isinstance(keys, str):
        keys = [k.strip() for k in keys.split(",")]
    return [k for k in list(keys) + [secret("GROQ_API_KEY")] if k]


NASA_API_KEY = secret("NASA_API_KEY", "DEMO_KEY")
SAFETY_FAIL_CLOSED = str(secret("SAFETY_FAIL_CLOSED", "false")).lower() == "true"

QUICK_TOPICS = {
    "☀️ The Sun": "Tell me about the Sun!",
    "🪐 Saturn's rings": "What are Saturn's rings made of?",
    "🌙 Our Moon": "How was our Moon made?",
    "🕳️ Black holes": "What is a black hole?",
    "👩‍🚀 Astronauts": "How do astronauts live on the space station?",
    "🔴 Mars": "Could people live on Mars one day?",
}

FUN_FACTS = [
    "A day on Venus is longer than a year on Venus! 🌕",
    "Footprints on the Moon can last millions of years because there's no wind. 👣",
    "Neutron stars are so heavy that a teaspoon would weigh about a billion tons! 🥄",
    "Saturn is so light it could float in a (really, really big) bathtub! 🛁",
    "There are more stars in the universe than grains of sand on all of Earth's beaches. ✨",
    "Astronauts grow up to 5 cm taller in space because their spine stretches! 📏",
    "Olympus Mons on Mars is almost 3 times taller than Mount Everest! 🏔️",
    "Light from the Sun takes about 8 minutes to reach Earth. ☀️",
]

CSS = """
<style>
.stApp { background: radial-gradient(ellipse at top, #1b2a55 0%, #0b1026 60%, #05060f 100%); color: #f2f4ff; }
h1, h2, h3, p, li, span, label { color: #f2f4ff !important; }
.fact-box { background: rgba(255,255,255,.08); border: 1px solid rgba(255,215,120,.5);
  border-radius: 16px; padding: 14px 18px; font-size: 1.1rem; margin-bottom: 12px; }
.rank-box { background: rgba(106,76,255,.18); border: 1px solid rgba(106,76,255,.6);
  border-radius: 16px; padding: 10px 14px; margin-bottom: 10px; }
div.stButton > button, div.stFormSubmitButton > button {
  border-radius: 20px; width: 100%; font-size: 1rem; font-weight: 600;
  background: linear-gradient(135deg, #6a4cff 0%, #3b82f6 100%) !important;
  color: #fff !important; border: 1px solid rgba(255,255,255,.25) !important; }
div.stButton > button p, div.stFormSubmitButton > button p { color: #fff !important; }
div.stButton > button:hover { background: linear-gradient(135deg, #ff7ac6 0%, #ffb347 100%) !important;
  border-color: #ffd166 !important; transform: scale(1.03); }
[data-testid="stTextInput"] input { background: #1b2a55 !important; color: #fff !important;
  -webkit-text-fill-color: #fff !important; font-size: 1.1rem; }
[data-testid="stSidebar"] { background: #121a3a; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stBottom"], [data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] { background: #0b1026 !important; }
[data-testid="stChatInput"] { background: #1b2a55 !important; border: 2px solid #6a4cff !important;
  border-radius: 20px !important; }
[data-testid="stChatInput"] > div { background: transparent !important; }
[data-testid="stChatInput"] textarea { background: #1b2a55 !important; color: #fff !important;
  caret-color: #ffd166 !important; -webkit-text-fill-color: #fff !important; font-size: 1.05rem !important; }
[data-testid="stChatInput"] textarea::placeholder { color: #aab4e8 !important; -webkit-text-fill-color: #aab4e8 !important; }
[data-testid="stChatMessage"] { background: rgba(255,255,255,.06); border-radius: 16px; font-size: 1.1rem; }
[data-testid="stAudioInput"] { background: #1b2a55; border-radius: 16px; }
[data-testid="stExpander"] { background: rgba(255,255,255,.05); border-radius: 16px; }
</style>
"""

st.set_page_config(page_title="Space Explorer", page_icon="🚀", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

if not groq_keys():
    st.error("No Groq key found. Add GROQ_API_KEYS (or GROQ_API_KEY) to the app's Secrets.")
    st.stop()


@st.cache_resource
def get_pool():
    """Shared by all visitors, so a dead key is skipped for everyone."""
    return KeyPool(groq_keys())


pool = get_pool()


# ---------- Cached NASA helpers ----------
@st.cache_data(ttl=3 * 3600, show_spinner=False)
def apod_today():
    return nasa.get_apod(NASA_API_KEY)


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def apod_for_kids(title, explanation):
    try:
        return pool.complete([{"role": "user", "content": APOD_PROMPT.format(title=title, explanation=explanation)}],
                             CHAT_MODELS, temperature=0.5, max_tokens=250)
    except Exception:
        return ""


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def nasa_image(query):
    return nasa.search_image(query)


def speak_button(text):
    """🔊 button that reads the answer aloud with the device's built-in voice (free, no API)."""
    safe = json.dumps(for_speech(text))
    components.html(f"""
    <button id="b" style="background:linear-gradient(135deg,#6a4cff,#3b82f6);color:#fff;border:0;
      border-radius:18px;padding:6px 14px;font-size:15px;font-weight:600;cursor:pointer">🔊 Read it to me</button>
    <script>
      const b = document.getElementById("b"); let on = false;
      b.onclick = () => {{
        const s = window.speechSynthesis;
        if (on) {{ s.cancel(); on = false; b.textContent = "🔊 Read it to me"; return; }}
        const u = new SpeechSynthesisUtterance({safe});
        u.rate = 0.95; u.pitch = 1.1;
        u.onend = () => {{ on = false; b.textContent = "🔊 Read it to me"; }};
        s.cancel(); s.speak(u); on = true; b.textContent = "⏹️ Stop";
      }};
    </script>""", height=48)


# ---------- Stars & ranks ----------
def add_stars(n):
    before = rank_for(st.session_state.stars)["name"]
    st.session_state.stars += n
    after = rank_for(st.session_state.stars)
    if after["name"] != before:
        st.session_state.rank_up = after


def show_rank():
    r = rank_for(st.session_state.get("stars", 0))
    nxt = f" · {r['next_at'] - r['stars']} ⭐ to <b>{r['next_name']}</b>" if r["next_name"] else " · Top rank! 🏆"
    st.markdown(f'<div class="rank-box">{r["emoji"]} <b>{r["name"]}</b> · ⭐ {r["stars"]}{nxt}</div>',
                unsafe_allow_html=True)
    st.progress(r["progress"])


# ---------- Welcome: ask the child's name (optional) ----------
if "name_done" not in st.session_state:
    st.title("🚀 Space Explorer")
    st.markdown("### Hi there, future astronaut! 👋")
    st.markdown("I'm **Cosmo**, your space agent. What's your first name?")
    with st.form("name_form"):
        typed_name = st.text_input("Your first name", max_chars=20, placeholder="e.g. Tanvi",
                                   label_visibility="collapsed")
        c1, c2 = st.columns(2)
        go = c1.form_submit_button("🚀 Blast off!")
        skip = c2.form_submit_button("Skip")
    if go or skip:
        st.session_state.kid_name = clean_name(typed_name) if go else ""
        st.session_state.name_done = True
        st.rerun()
    st.caption("🔒 Just your first name, please. Never share your address, school or phone number online.")
    st.stop()

ss = st.session_state
ss.setdefault("messages", [])
ss.setdefault("stars", 0)
ss.setdefault("asked", 0)
ss.setdefault("voice_n", 0)
ss.setdefault("quiz", None)
ss.setdefault("fact", random.choice(FUN_FACTS))
kid_name = ss.get("kid_name", "")

# ---------- Header ----------
st.title("🚀 Space Explorer")
st.caption(f"Hi {kid_name or 'Space Explorer'}! I'm Cosmo, your space agent. Ask me anything about space! 🌌")

if ss.get("rank_up"):
    r = ss.pop("rank_up")
    st.balloons()
    st.success(f"🎉 Level up! You are now a **{r['name']}** {r['emoji']}")

show_rank()

col1, col2 = st.columns([5, 1])
with col1:
    st.markdown(f'<div class="fact-box">🌟 <b>Fun fact:</b> {ss.fact}</div>', unsafe_allow_html=True)
with col2:
    if st.button("🔄", help="New fun fact"):
        ss.fact = random.choice(FUN_FACTS)
        st.rerun()

with st.expander("🔭 NASA's Space Picture of the Day"):
    apod = apod_today()
    if apod and apod.get("image"):
        st.image(apod["image"], caption=f"{apod['title']} · {apod['date']}")
        kids = apod_for_kids(apod["title"], apod["explanation"])
        st.markdown(kids or apod["explanation"][:400] + "…")
        credit = f"Image credit: {apod['copyright']}" if apod.get("copyright") else "Image credit: NASA"
        st.caption(f"{credit} · [See it bigger]({apod['link']})")
    else:
        st.write("NASA's picture is still on its way from space. Try again later! 🛰️")

st.markdown("**Pick a topic, type, or use your voice:**")
clicked = None
cols = st.columns(3)
for i, (label, question) in enumerate(QUICK_TOPICS.items()):
    if cols[i % 3].button(label, key=f"topic_{i}"):
        clicked = question

# ---------- Chat history ----------
last_answer_idx = max((i for i, m in enumerate(ss.messages) if m["role"] == "assistant"), default=-1)
for i, msg in enumerate(ss.messages):
    with st.chat_message(msg["role"], avatar="🧑‍🚀" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])
        if msg.get("image"):
            st.image(msg["image"]["url"], width=320, caption=f"{msg['image']['title']} · Image: NASA")
        if i == last_answer_idx:
            speak_button(msg["content"])

# ---------- Quiz ----------
# Only real space answers count as lessons (not greetings, refusals, blocked or error replies)
lessons = [(ss.messages[i - 1]["content"], m["content"]) for i, m in enumerate(ss.messages)
           if m["role"] == "assistant" and m.get("learned") and i > 0]
if lessons and ss.quiz is None:
    if st.button("🧠 Quiz me on what I learned! (+1 ⭐ per right answer)"):
        with st.spinner("Cosmo is making your quiz... 🧠"):
            try:
                questions = make_quiz(pool, lessons[-3:])
            except Exception as e:
                print("Quiz failed:", e)
                questions = []
        if questions:
            ss.quiz = {"questions": questions, "result": None}
            st.rerun()
        else:
            st.warning("Cosmo couldn't make a quiz this time. Ask another question and try again!")

if ss.quiz:
    st.markdown("### 🧠 Space Quiz")
    qz = ss.quiz
    if qz["result"] is None:
        with st.form("quiz_form"):
            picks = [st.radio(f"**{n + 1}. {q['question']}**", q["options"], index=None, key=f"q{n}")
                     for n, q in enumerate(qz["questions"])]
            done = st.form_submit_button("✅ Check my answers")
        if done:
            right = sum(1 for q, p in zip(qz["questions"], picks, strict=True) if p == q["options"][q["answer"]])
            qz["result"] = {"picks": picks, "right": right}
            add_stars(right)
            st.rerun()
    else:
        res = qz["result"]
        for q, p in zip(qz["questions"], res["picks"], strict=True):
            correct = q["options"][q["answer"]]
            st.markdown(f"{'✅' if p == correct else '❌'} **{q['question']}**  \nAnswer: **{correct}**. {q['explain']}")
        total = len(qz["questions"])
        st.success(f"You got **{res['right']} / {total}** right and earned {res['right']} ⭐!"
                   + (" Perfect score! 🏆" if res["right"] == total else ""))
        if st.button("👍 Done, back to exploring"):
            ss.quiz = None
            st.rerun()

# ---------- Voice question ----------
voice_text = None
audio = st.audio_input("🎤 Tap the mic and ask Cosmo out loud", key=f"voice_{ss.voice_n}")
if audio is not None:
    data = audio.getvalue()
    digest = hashlib.md5(data).hexdigest()
    if digest != ss.get("last_audio"):
        ss.last_audio = digest
        with st.spinner("Cosmo is listening... 👂"):
            try:
                voice_text = pool.transcribe(data, WHISPER_MODELS)
            except Exception as e:
                print("Transcription failed:", e)
                voice_text = ""
        ss.voice_n += 1  # fresh mic for the next question
        if not voice_text:
            st.warning("I couldn't hear that. Try again a bit closer to the mic! 🎤")
st.caption("🎤 Your voice is turned into text by Groq and is not saved.")

typed = st.chat_input("Ask Cosmo about planets, stars, rockets...")
prompt = typed or clicked or voice_text

# ---------- Answer ----------
if prompt:
    prompt = prompt.strip()[:MAX_QUESTION_CHARS]
    ss.quiz = None  # a new question closes any old quiz (finished or not)
    ss.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍🚀"):
        st.markdown(("🎤 " if voice_text else "") + prompt)
    with st.chat_message("assistant", avatar="🤖"):
        meta = {}
        if ss.asked >= MAX_QUESTIONS_PER_VISIT:
            answer = ("🌙 Wow, you asked so many great questions! Cosmo needs to recharge. "
                      "Come back later for more space adventures!")
            st.markdown(answer)
        else:
            ss.asked += 1
            answer = st.write_stream(pipeline.respond(pool, ss.messages, kid_name, meta,
                                                      fail_closed=SAFETY_FAIL_CLOSED))
        entry = {"role": "assistant", "content": answer}
        if meta.get("ok") and not is_refusal(answer) and not is_blocked(answer):
            query = nasa.image_query_for(prompt) or nasa.image_query_for(answer)
            img = nasa_image(query) if query else None
            if img:
                st.image(img["url"], width=320, caption=f"{img['title']} · Image: NASA")
                entry["image"] = img
            entry["learned"] = not is_chitchat(prompt)
            if entry["learned"]:
                add_stars(1)
    ss.messages.append(entry)
    st.rerun()  # redraw so rank, quiz button and history are up to date

# ---------- Sidebar ----------
with st.sidebar:
    st.header("🛰️ Mission Control")
    if st.button("🧹 Start a new chat"):
        ss.messages, ss.quiz = [], None
        st.rerun()
    if st.button("👋 New explorer"):
        for k in list(ss.keys()):
            del ss[k]
        st.rerun()
    st.markdown("---")
    st.markdown("Made with ❤️ for future astronauts 👩‍🚀🧑‍🚀")
    st.caption(f"Space Explorer v{__version__} · Pictures: NASA")
