"""
Instaptly — Streamlit entry point for Streamlit Community Cloud.

This reuses the caption/hashtag logic from app.py (the Flask version) and
wraps it in a Streamlit UI. Streamlit Cloud runs `streamlit run streamlit_app.py`.

API KEY
  On Streamlit Cloud, add your key under  Manage app → Settings → Secrets  as:
      ANTHROPIC_API_KEY = "sk-ant-..."
  Locally, either add it to .streamlit/secrets.toml or export it as an env var.
  If no key is present, the app automatically falls back to free MOCK captions.

Palette: "Sunset Pop"  (#FF5E62 / #FF9966 / #FFD166 / #2B2D42 / #FFF3EC)
"""

import os
import streamlit as st

from app import (
    TONES,
    generate_captions_mock,
    generate_captions_ai,
)

# ---------------------------------------------------------------------------
# API KEY: pull from Streamlit Secrets into the env var that app.py reads.
# Real AI turns on automatically when a key is available; otherwise mock mode.
# ---------------------------------------------------------------------------
try:
    if "ANTHROPIC_API_KEY" in st.secrets:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    # st.secrets raises if no secrets file exists at all — that's fine.
    pass

USE_REAL_AI = bool(os.environ.get("ANTHROPIC_API_KEY"))

# ---------------------------------------------------------------------------
# PAGE + STYLE
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Instaptly", page_icon="✨", layout="centered")

st.markdown(
    """
    <style>
      :root { --coral:#FF5E62; --peach:#FF9966; --gold:#FFD166;
              --ink:#2B2D42; --cream:#FFF3EC; }
      .stApp { background: var(--cream); }
      h1 { color: var(--ink); }
      .tagline { color: var(--ink); opacity:.75; margin-top:-.6rem; }
      .stButton>button {
          background: linear-gradient(90deg,var(--coral),var(--peach));
          color: white; border: none; border-radius: 999px;
          padding: .5rem 1.4rem; font-weight: 600;
      }
      .stButton>button:hover { filter: brightness(1.05); }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("# Instaptly ✨")
st.markdown(
    '<p class="tagline">Upload a pic, pick a vibe, get post-ready captions '
    "+ reach-optimized hashtags.</p>",
    unsafe_allow_html=True,
)

mode_label = "🟢 Real AI" if USE_REAL_AI else "🟡 Mock mode (no API key set)"
st.caption(f"Mode: {mode_label}")

# ---------------------------------------------------------------------------
# CONTROLS
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    tone = st.selectbox("Vibe", TONES, index=TONES.index("Aesthetic"))
with col2:
    tags_per = st.slider("Hashtags per caption", 0, 10, 3)

photo = st.file_uploader(
    "Photo", type=["png", "jpg", "jpeg", "webp"], help="Your photo is never stored."
)

if photo is not None:
    st.image(photo, caption="Preview", use_container_width=True)

go = st.button("✨ Generate captions", disabled=(photo is None))

# ---------------------------------------------------------------------------
# GENERATE
# ---------------------------------------------------------------------------
if go and photo is not None:
    with st.spinner("Cooking up captions…"):
        try:
            if USE_REAL_AI:
                image_bytes = photo.getvalue()  # in memory only, never saved
                captions = generate_captions_ai(
                    image_bytes, photo.type, tone, tags_per_caption=tags_per
                )
            else:
                captions = generate_captions_mock(tone, tags_per_caption=tags_per)
        except Exception as e:  # noqa: BLE001 — surface any API/parse error to the user
            st.error(f"Something went wrong generating captions: {e}")
            captions = []

    if captions:
        st.subheader(f"{tone} captions")
        for i, cap in enumerate(captions, 1):
            text = cap.get("text", "")
            tags = " ".join(cap.get("hashtags", []))
            block = text if not tags else f"{text}\n\n{tags}"
            st.markdown(f"**{i}.**")
            st.code(block, language=None)  # st.code gives a one-click copy button
