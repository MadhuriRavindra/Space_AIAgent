"""
🚀 Space Explorer: a kid-friendly space Q&A app
Streamlit UI + Groq LLM
"""
import random
import streamlit as st
from groq import Groq


# ---------- Config helpers ----------
def secret(key, default=None):
    """Read from Streamlit secrets without crashing if no secrets file exists."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


KID_NAME = secret("KID_NAME", "Space Explorer")
GROQ_API_KEY = secret("GROQ_API_KEY")
APP_PASSCODE = secret("APP_PASSCODE")  # optional: protects your Groq key
# Tried in order; if one model is retired or rate-limited, the next is used.
MODELS = [
    secret("GROQ_MODEL", "llama-3.3-70b-versatile"),
    "openai/gpt-oss-120b",
    "llama-3.1-8b-instant",
]

SYSTEM_PROMPT = f"""You are "Cosmo", a friendly, enthusiastic space guide for a 10-year-old girl named {KID_NAME} who dreams of becoming an astronaut.

HOW TO ANSWER:
- Use simple words a 10-year-old understands. Explain any big word right away in brackets.
- Keep answers short: 4 to 8 sentences, or a few bullet points.
- Use fun comparisons from everyday life (e.g. "Jupiter is so big that 1,300 Earths could fit inside it!").
- Add 1-2 relevant emojis, not more.
- End with one "🌟 Wow Fact:" line and, sometimes, a short question to spark her curiosity.
- Be scientifically accurate. If scientists don't know something yet, say so. That's exciting!
- Be encouraging about her dream of becoming an astronaut when it fits naturally.

TOPICS: space, the solar system, planets, moons, stars, galaxies, black holes, rockets, astronauts, space missions, telescopes, and related science.

SAFETY RULES:
- If she asks about something unrelated to space or science, gently say you're a space guide and steer back with a fun space idea.
- Never ask for or discuss personal information (address, school, phone, etc.).
- Keep scary topics (e.g. asteroids hitting Earth, black holes) calm and reassuring, with facts.
- No violent, adult, or inappropriate content, ever.
"""

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


# ---------- Page & style ----------
st.set_page_config(page_title="Space Explorer", page_icon="🚀", layout="centered")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(ellipse at top, #1b2a55 0%, #0b1026 60%, #05060f 100%);
        color: #f2f4ff;
    }
    h1, h2, h3, p, li, span, label { color: #f2f4ff !important; }
    .fact-box {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 215, 120, 0.5);
        border-radius: 16px;
        padding: 14px 18px;
        font-size: 1.1rem;
        margin-bottom: 12px;
    }
    div.stButton > button {
        border-radius: 20px;
        width: 100%;
        font-size: 1rem;
        font-weight: 600;
        background: linear-gradient(135deg, #6a4cff 0%, #3b82f6 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
    }
    div.stButton > button p { color: #ffffff !important; }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #ff7ac6 0%, #ffb347 100%) !important;
        border-color: #ffd166 !important;
        transform: scale(1.03);
    }
    [data-testid="stSidebar"] { background: #121a3a; }
    [data-testid="stHeader"] { background: transparent; }
    /* Chat input area at the bottom */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] { background: #0b1026 !important; }
    [data-testid="stChatInput"] {
        background: #1b2a55 !important;
        border: 2px solid #6a4cff !important;
        border-radius: 20px !important;
    }
    [data-testid="stChatInput"] > div { background: transparent !important; }
    [data-testid="stChatInput"] textarea {
        background: #1b2a55 !important;
        color: #ffffff !important;
        caret-color: #ffd166 !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 1.05rem !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #aab4e8 !important;
        -webkit-text-fill-color: #aab4e8 !important;
    }
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        font-size: 1.1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Optional passcode gate ----------
if APP_PASSCODE and not st.session_state.get("unlocked"):
    st.title("🚀 Space Explorer")
    code = st.text_input("Enter the secret launch code 🔐", type="password")
    if code:
        if code == APP_PASSCODE:
            st.session_state.unlocked = True
            st.rerun()
        else:
            st.error("Oops, wrong code! Try again 🛸")
    st.stop()

if not GROQ_API_KEY:
    st.error("GROQ_API_KEY is missing. Add it to .streamlit/secrets.toml or the app's Secrets settings.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)


# ---------- LLM call with streaming + model fallback ----------
def ask_cosmo(history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-10:]
    last_error = None
    for model in MODELS:
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.6,
                max_tokens=600,
                stream=True,
            )
            for chunk in stream:
                yield chunk.choices[0].delta.content or ""
            return
        except Exception as e:  # model retired / rate limit → try next
            last_error = e
            continue
    yield f"😕 Cosmo's radio is fuzzy right now. Please try again in a minute! ({last_error})"


# ---------- UI ----------
st.title("🚀 Space Explorer")
st.caption(f"Hi {KID_NAME}! I'm Cosmo, your space guide. Ask me anything about space! 🌌")

if "fact" not in st.session_state:
    st.session_state.fact = random.choice(FUN_FACTS)

col1, col2 = st.columns([5, 1])
with col1:
    st.markdown(f'<div class="fact-box">🌟 <b>Fun fact:</b> {st.session_state.fact}</div>',
                unsafe_allow_html=True)
with col2:
    if st.button("🔄", help="New fun fact"):
        st.session_state.fact = random.choice(FUN_FACTS)
        st.rerun()

st.markdown("**Pick a topic or type your own question:**")
clicked = None
cols = st.columns(3)
for i, (label, question) in enumerate(QUICK_TOPICS.items()):
    if cols[i % 3].button(label, key=f"topic_{i}"):
        clicked = question

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    avatar = "👧" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

typed = st.chat_input("Ask Cosmo about planets, stars, rockets...")
prompt = typed or clicked

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👧"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar="🤖"):
        answer = st.write_stream(ask_cosmo(st.session_state.messages))
    st.session_state.messages.append({"role": "assistant", "content": answer})

with st.sidebar:
    st.header("🛰️ Mission Control")
    if st.button("🧹 Start a new chat"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.markdown("Made with ❤️ for a future astronaut 👩‍🚀")