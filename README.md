# Instaptly ✨

A photo-first Instagram caption generator. Upload a pic, pick a vibe, and get
post-ready captions with reach-optimized hashtags. Prototype built with Flask.

Palette: **Sunset Pop** — `#FF5E62` · `#FF9966` · `#FFD166` · `#2B2D42` · `#FFF3EC`

## Features
- Drag-and-drop photo upload with instant preview
- Six vibes: Funny · Aesthetic · Minimal · Bold · Inspirational · Story
- Adjustable hashtags-per-caption slider (0–10)
- Copy caption + hashtags, or hashtags only
- **Mock mode** (default): full clickable flow with no API key, no cost
- **Real AI mode**: sends the photo to a vision model in memory — never
  written to disk

## Quick start
```bash
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000

Out of the box it runs in **mock mode**, so you can click the whole flow
immediately with no setup.

## Turning on real AI
1. Get an Anthropic API key: https://console.anthropic.com
2. Set it as an environment variable:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."     # Windows: set ANTHROPIC_API_KEY=...
   ```
3. In `app.py`, change:
   ```python
   USE_REAL_AI = True
   ```
4. Restart the app. Now real captions + hashtags are generated from the photo.

The API key lives only on the server — it's never exposed to the browser.

## How the "no image storage" works
When real AI is on, the uploaded photo is read into memory, base64-encoded,
sent to the model, and then goes out of scope — it is never saved to disk or a
database. This is the ephemeral / stateless approach, so you can truthfully
tell users their photos aren't stored. (Note: with a third-party API the image
does pass *through* the provider's servers to be analyzed; use a zero-retention
tier if you want a fully clean "stored nowhere" claim.)

## Project structure
```
app.py             # Flask app + UI + caption/hashtag logic
requirements.txt   # dependencies
README.md          # this file
```

## Config (top of app.py)
| Setting            | What it does                                  |
|--------------------|-----------------------------------------------|
| `USE_REAL_AI`      | `False` = mock captions, `True` = real model  |
| `ANTHROPIC_MODEL`  | Which model to call                            |
| `MAX_UPLOAD_MB`    | Reject uploads larger than this                |
| `TONES`            | The vibe options shown in the UI               |

## Deploying
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
