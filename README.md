# Instaptly ✨

A photo-first Instagram caption generator. Upload a pic, pick a vibe, and get
post-ready captions with reach-optimized hashtags.

It ships with **two front-ends** that share the same caption engine:

- **Flask** (`app.py`) — the original prototype, runs locally as a web app.
- **Streamlit** (`streamlit_app.py`) — a styled UI ready to deploy to
  [Streamlit Community Cloud](https://share.streamlit.io/) in a few clicks.

Palette: **Sunset Pop** — `#FF5E62` · `#FF9966` · `#FFD166` · `#2B2D42` · `#FFF3EC`

## Features
- Drag-and-drop photo upload with instant preview
- Six vibes: Funny · Aesthetic · Minimal · Bold · Inspirational · Story
- Adjustable hashtags-per-caption slider (0–10)
- Copy caption + hashtags with one click
- **Mock mode** (default): full clickable flow with no API key, no cost
- **Real AI mode**: sends the photo to a vision model in memory — never
  written to disk

## Quick start

Install dependencies once:
```bash
pip install -r requirements.txt
```

### Run the Streamlit app (recommended)
```bash
streamlit run streamlit_app.py
```
Opens at http://localhost:8501

### Run the Flask app
```bash
python app.py
```
Then open http://127.0.0.1:5000

Out of the box **both** run in **mock mode**, so you can click the whole flow
immediately with no setup.

## Turning on real AI

Get an Anthropic API key first: https://console.anthropic.com

**Streamlit** — provide the key as a secret; real AI turns on automatically
when a key is present (no code change needed):

- Locally, create `.streamlit/secrets.toml`:
  ```toml
  ANTHROPIC_API_KEY = "sk-ant-..."
  ```
- On Streamlit Cloud, add the same under **Manage app → Settings → Secrets**.

**Flask** — set the env var and flip the flag in `app.py`:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."     # Windows: set ANTHROPIC_API_KEY=...
```
```python
USE_REAL_AI = True
```
Then restart the app.

The API key lives only on the server — it's never exposed to the browser.
**Don't commit your key.** `.streamlit/secrets.toml` is gitignored for that reason.

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub (already done if you're reading this on GitHub).
2. Go to https://share.streamlit.io/ and click **Create app**.
3. Set:
   - **Repository:** `<your-user>/instaptly`
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
4. Under **Advanced settings → Secrets**, add:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
   (Skip this to run the deployed app in free mock mode.)
5. Click **Deploy**. You'll get a public `https://<app>.streamlit.app` URL.

Every push to `main` auto-redeploys the app.

> ⚠️ A deployed app is public — anyone with the URL can trigger API calls.
> Set a spend cap in the Anthropic console and rotate your key if it's ever
> exposed.

## How the "no image storage" works
When real AI is on, the uploaded photo is read into memory, base64-encoded,
sent to the model, and then goes out of scope — it is never saved to disk or a
database. This is the ephemeral / stateless approach, so you can truthfully
tell users their photos aren't stored. (Note: with a third-party API the image
does pass *through* the provider's servers to be analyzed; use a zero-retention
tier if you want a fully clean "stored nowhere" claim.)

## Project structure
```
app.py             # Flask app + UI + shared caption/hashtag logic
streamlit_app.py   # Streamlit UI (reuses app.py's logic) — Cloud entry point
requirements.txt   # dependencies (streamlit, flask, anthropic)
README.md          # this file
```

## Config (top of app.py)
| Setting            | What it does                                  |
|--------------------|-----------------------------------------------|
| `USE_REAL_AI`      | `False` = mock captions, `True` = real model (Flask only; the Streamlit app decides automatically based on whether a key is present) |
| `ANTHROPIC_MODEL`  | Which model to call                            |
| `MAX_UPLOAD_MB`    | Reject uploads larger than this                |
| `TONES`            | The vibe options shown in the UI               |

## Deploying the Flask version elsewhere
Any host that runs Python works (Render, Railway, Fly.io, a VPS). Use a
production server instead of the dev server, e.g.:
```bash
pip install gunicorn
gunicorn app:app
```
Set `ANTHROPIC_API_KEY` in the host's environment variables — don't commit it.

## Ideas for next
- Save favorites / caption history (opt-in, since default is no storage)
- Personal "voice memory" so captions sound like you
- Carousel / Story / Reel caption modes
- Rate limiting for a public free tier
