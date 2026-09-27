# 🚀 Space Explorer

A kid-friendly space Q&A app. Streamlit UI + Groq LLM.

## Architecture

```
 Phone / Tablet / Laptop (any browser)
            │  HTTPS
            ▼
 Streamlit Community Cloud (free hosting)
   └── app.py
        ├── Passcode gate (optional)
        ├── UI: fun fact, topic buttons, chat
        ├── Session memory (last 10 messages)
        └── Kid-safe system prompt ("Cosmo")
            │  Groq API (streaming)
            ▼
   Groq LLM: llama-3.3-70b → gpt-oss-120b → llama-3.1-8b (fallback)
```

Files: `app.py`, `requirements.txt`, `.streamlit/secrets.toml` (local only).

## Run locally (5 min)

```bash
mkdir space-explorer && cd space-explorer
# put app.py and requirements.txt here
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
mkdir .streamlit
# create .streamlit/secrets.toml from secrets.toml.example with your Groq key
streamlit run app.py
```

## Deploy (10 min), open from any device

1. Create a **GitHub repo** and push `app.py` + `requirements.txt`.
   Add a `.gitignore` containing `.streamlit/secrets.toml` so the key is never committed.
2. Go to **share.streamlit.io** → sign in with GitHub → **Create app**.
3. Pick the repo, branch `main`, main file `app.py`.
4. **Advanced settings → Secrets**: paste the contents of `secrets.toml.example` with your real values.
5. Click **Deploy**. You get a URL like `https://space-explorer-xyz.streamlit.app`.
6. On her tablet/phone: open the URL → browser menu → **Add to Home Screen**. It then works like an app icon.

Tips:
- Keep `APP_PASSCODE` set; the URL is public, and the passcode protects your Groq quota.
- Free Streamlit apps sleep after inactivity; the first open may take ~30 seconds to wake.
- If Groq retires a model, the app falls back automatically; you can also set `GROQ_MODEL` in Secrets.