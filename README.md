# 🚀 Space Explorer

A safe, kid-friendly space guide. Children aged 7–12 ask **Cosmo** anything about space by typing or talking. They get simple answers, real NASA photos, quizzes and space ranks.

## Features

| For children | Under the hood |
|---|---|
| 🎤 Ask with your voice, 🔊 hear the answer | Groq Whisper speech-to-text; browser speech synthesis (free, no API) |
| 🖼️ Real NASA photo with answers + Picture of the Day | NASA Images API + APOD API, cached |
| 🧠 "Quiz me!" + ⭐ stars and ranks | Quiz generated as JSON from the child's own answers, validated |
| 🛡️ Safe and on-topic | GPT-OSS-Safeguard child-safety policy + strict system prompt |
| Always available | Several Groq keys with automatic switching + model fallback |

## Architecture

```
 Child's phone / tablet
        │  text or 🎤 voice ──► Groq Whisper ──► text
        ▼
 Streamlit app (app.py)
        │
        ▼
 cosmo/pipeline.py ── 1. safety check ──► GPT-OSS-Safeguard (child-safety policy)
        │                    │ unsafe ──► kind "talk to a grown-up" reply
        │ safe               
        ▼
 2. Cosmo answers ──► Llama 3.3 70B → GPT-OSS 120B → Llama 3.1 8B   (key rotation per model)
        │
        ▼
 3. NASA photo (images-api.nasa.gov) · 🔊 read aloud · ⭐ star · 🧠 quiz
```

```
cosmo/          llm.py (key pool, streaming, fallback) · safety.py · pipeline.py
                nasa.py · quiz.py · ranks.py · text.py · prompts.py
tests/          51 offline tests with a fake Groq (incl. clicking through the app)
evals/          cases.json (48 cases) · run.py (live quality & safety gate)
.github/        ci.yml (test → eval → promote) · release.yml · rollback.yml
```

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp secrets.toml.example .streamlit/secrets.toml       # add your Groq keys
streamlit run app.py
pytest -q                                             # offline tests
GROQ_API_KEY=gsk_... python -m evals.run --limit 10   # live eval (quick)
```

## Deploy

See [RELEASE.md](RELEASE.md). In short: Streamlit Cloud serves the **`release`** branch, and only the CI/CD pipeline updates it, after tests and the AI quality & safety gate pass.

## Privacy

No accounts, no database. Only a first name (optional), kept in the browser session. Voice recordings are transcribed by Groq and not stored by the app.
