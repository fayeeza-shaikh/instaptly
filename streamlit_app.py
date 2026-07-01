"""
Instaptly — Streamlit entry point for Streamlit Community Cloud.

This reuses the caption/hashtag logic from app.py (the Flask version) and
wraps it in a styled Streamlit UI. Streamlit Cloud runs
`streamlit run streamlit_app.py`.

API KEY
  On Streamlit Cloud, add your key under  Manage app → Settings → Secrets  as:
      ANTHROPIC_API_KEY = "sk-ant-..."
  Locally, either add it to .streamlit/secrets.toml or export it as an env var.
  If no key is present, the app automatically falls back to free MOCK captions.

Palette: "Sunset Pop"  (#FF5E62 / #FF9966 / #FFD166 / #2B2D42 / #FFF3EC)
"""

import html
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
# PAGE + STYLE  (Sunset Pop)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Instaptly", page_icon="✨", layout="centered")

st.markdown(
    """
    <style>
      :root { --coral:#FF5E62; --peach:#FF9966; --gold:#FFD166;
              --ink:#2B2D42; --cream:#FFF3EC; }

      .stApp { background: var(--cream); }

      /* Hero header */
      .hero {
          background: linear-gradient(120deg, var(--coral), var(--peach) 55%, var(--gold));
          border-radius: 22px;
          padding: 28px 30px;
          color: white;
          box-shadow: 0 12px 30px rgba(255,94,98,.28);
          margin-bottom: 18px;
      }
      .hero h1 { margin: 0; font-size: 2.4rem; font-weight: 800; letter-spacing:-.5px; }
      .hero p  { margin: 6px 0 0; font-size: 1.02rem; opacity: .95; }
      .hero .mode {
          display:inline-block; margin-top:14px; padding:4px 12px;
          background: rgba(255,255,255,.22); border-radius:999px;
          font-size:.8rem; font-weight:600;
      }

      /* Buttons */
      .stButton>button {
          background: linear-gradient(90deg,var(--coral),var(--peach));
          color: white; border: none; border-radius: 999px;
          padding: .55rem 1.5rem; font-weight: 700; width: 100%;
          box-shadow: 0 6px 16px rgba(255,94,98,.25);
      }
      .stButton>button:hover:enabled { filter: brightness(1.05); transform: translateY(-1px); }
      .stButton>button:disabled { opacity:.55; }

      /* Caption cards */
      .cap-card {
          background: white; border-radius: 18px; padding: 18px 20px;
          margin-bottom: 14px; border: 1px solid #ffe3d3;
          box-shadow: 0 6px 18px rgba(43,45,66,.06);
      }
      .cap-num {
          display:inline-flex; align-items:center; justify-content:center;
          width:26px; height:26px; border-radius:50%;
          background: linear-gradient(90deg,var(--coral),var(--peach));
          color:white; font-size:.8rem; font-weight:700; margin-right:8px;
      }
      .cap-text { color: var(--ink); font-size:1.08rem; font-weight:600; line-height:1.45; }
      .pill {
          display:inline-block; margin:6px 6px 0 0; padding:4px 11px;
          background: var(--cream); color:#c94b3b; border:1px solid #ffd9c6;
          border-radius:999px; font-size:.82rem; font-weight:600;
      }
      .divider { height:1px; background:#f3ddce; margin:12px 0 10px; border:0; }
    </style>
    """,
    unsafe_allow_html=True,
)

mode_label = "🟢 Real AI" if USE_REAL_AI else "🟡 Mock mode — no API key set"
st.markdown(
    f"""
    <div class="hero">
      <h1>Instaptly ✨</h1>
      <p>Upload a pic, pick a vibe, get post-ready captions + reach-optimized hashtags.</p>
      <span class="mode">{mode_label}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

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
            text = html.escape(cap.get("text", ""))
            pills = "".join(
                f'<span class="pill">{html.escape(t)}</span>'
                for t in cap.get("hashtags", [])
            )
            tag_html = f'<hr class="divider">{pills}' if pills else ""
            st.markdown(
                f"""
                <div class="cap-card">
                  <div class="cap-text"><span class="cap-num">{i}</span>{text}</div>
                  {tag_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
            # A plain copyable block (st.code has a one-click copy button)
            copy_text = cap.get("text", "")
            tags = " ".join(cap.get("hashtags", []))
            with st.expander("📋 Copy"):
                st.code(copy_text if not tags else f"{copy_text}\n\n{tags}", language=None)
