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

# Emoji per vibe, used in the chip picker and result heading.
VIBE_EMOJI = {
    "Funny": "😂",
    "Aesthetic": "🌅",
    "Minimal": "🤍",
    "Bold": "⚡",
    "Inspirational": "🌱",
    "Story": "📖",
}

# ---------------------------------------------------------------------------
# PAGE + STYLE  (Sunset Pop)
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Instaptly", page_icon="✨", layout="centered")

st.markdown(
"""
<style>
      @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&display=swap');
      :root { --coral:#FF5E62; --peach:#FF9966; --gold:#FFD166;
              --ink:#2B2D42; --cream:#FFF3EC; }

      html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
      .stApp { background:
          radial-gradient(1200px 500px at 80% -10%, #ffe9db 0%, transparent 60%),
          var(--cream); }

      /* Animated gradient hero */
      .hero {
          position: relative; overflow: hidden;
          background: linear-gradient(120deg, var(--coral), var(--peach), var(--gold), var(--coral));
          background-size: 300% 300%;
          animation: flow 12s ease infinite;
          border-radius: 26px; padding: 34px 34px 30px;
          color: white; box-shadow: 0 18px 40px rgba(255,94,98,.30);
          margin-bottom: 22px;
      }
      @keyframes flow {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
      }
      .hero h1 { margin:0; font-size:2.9rem; font-weight:800; letter-spacing:-1px;
                 text-shadow: 0 2px 12px rgba(0,0,0,.12); }
      .hero p  { margin:10px 0 0; font-size:1.08rem; opacity:.97; max-width:42ch; }
      .hero .mode { display:inline-flex; align-items:center; gap:7px; margin-top:16px;
                    padding:5px 14px; background:rgba(255,255,255,.22);
                    border:1px solid rgba(255,255,255,.35); border-radius:999px;
                    font-size:.82rem; font-weight:600; backdrop-filter: blur(4px); }
      .dot { width:9px; height:9px; border-radius:50%; display:inline-block; }
      .dot.on { background:#7CFC7C; box-shadow:0 0 8px #7CFC7C; }
      .dot.off { background:#FFE08A; box-shadow:0 0 8px #FFE08A; }

      /* Section labels */
      h3.section { color:var(--ink); font-weight:700; margin:.2rem 0 .6rem; }

      /* Buttons */
      .stButton>button {
          background: linear-gradient(90deg,var(--coral),var(--peach));
          color:white; border:none; border-radius:999px;
          padding:.62rem 1.6rem; font-weight:700; font-size:1.02rem; width:100%;
          box-shadow:0 8px 20px rgba(255,94,98,.28); transition:.15s;
      }
      .stButton>button:hover:enabled { filter:brightness(1.06); transform:translateY(-1px); }
      .stButton>button:disabled { opacity:.5; }

      /* Vibe chips (radio) — force a single horizontal row, no wrapping */
      div[role="radiogroup"] {
          display:flex !important; flex-direction:row !important;
          flex-wrap:nowrap !important; gap:7px; align-items:center;
          overflow-x:auto; padding-bottom:4px;
      }
      div[role="radiogroup"] label {
          background:white; border:1.5px solid #ffdcc9; border-radius:999px;
          padding:5px 12px; cursor:pointer; transition:.15s; font-weight:600;
          color:var(--ink); white-space:nowrap; flex:0 0 auto;
      }
      div[role="radiogroup"] label:hover { border-color:var(--peach); }
      div[role="radiogroup"] label:has(input:checked) {
          background:linear-gradient(90deg,var(--coral),var(--peach));
          color:white; border-color:transparent;
          box-shadow:0 6px 14px rgba(255,94,98,.25);
      }
      div[role="radiogroup"] label > div:first-child { display:none; } /* hide the dot */

      /* How-it-works strip */
      .steps { display:flex; gap:12px; margin:6px 0 4px; }
      .step { flex:1; background:white; border:1px solid #ffe3d3; border-radius:16px;
              padding:14px 16px; box-shadow:0 6px 16px rgba(43,45,66,.05); }
      .step .n { font-size:1.4rem; }
      .step .t { color:var(--ink); font-weight:700; margin-top:4px; font-size:.95rem; }
      .step .d { color:#6b6f80; font-size:.83rem; margin-top:2px; }

      /* Caption cards */
      .cap-card { background:white; border-radius:20px; padding:20px 22px;
                  margin-bottom:14px; border:1px solid #ffe3d3;
                  box-shadow:0 8px 22px rgba(43,45,66,.07); }
      .cap-num { display:inline-flex; align-items:center; justify-content:center;
                 width:28px; height:28px; border-radius:50%;
                 background:linear-gradient(90deg,var(--coral),var(--peach));
                 color:white; font-size:.85rem; font-weight:700; margin-right:10px; }
      .cap-text { color:var(--ink); font-size:1.12rem; font-weight:600; line-height:1.5; }
      .pill { display:inline-block; margin:7px 6px 0 0; padding:4px 12px;
              background:var(--cream); color:#c94b3b; border:1px solid #ffd9c6;
              border-radius:999px; font-size:.83rem; font-weight:600; }
      .divider { height:1px; background:#f3ddce; margin:13px 0 10px; border:0; }

      .foot { text-align:center; color:#9a8f88; font-size:.82rem; margin-top:28px; }
      .foot a { color:#c94b3b; text-decoration:none; font-weight:600; }
    </style>
    """,
    unsafe_allow_html=True,
)

if USE_REAL_AI:
    mode_html = '<span class="dot on"></span> Real AI'
else:
    mode_html = '<span class="dot off"></span> Mock mode — no API key set'

st.markdown(
    f"""
    <div class="hero">
      <h1>Instaptly ✨</h1>
      <p>Upload a pic, pick a vibe, and get post-ready captions with
         reach-optimized hashtags — in seconds.</p>
      <span class="mode">{mode_html}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# CONTROLS
# ---------------------------------------------------------------------------
st.markdown('<h3 class="section">1 · Pick a vibe</h3>', unsafe_allow_html=True)
vibe_labels = [f"{VIBE_EMOJI.get(t, '')} {t}".strip() for t in TONES]
chosen = st.radio(
    "Vibe", vibe_labels, index=TONES.index("Aesthetic"),
    horizontal=True, label_visibility="collapsed",
)
tone = TONES[vibe_labels.index(chosen)]

tags_per = st.slider("Hashtags per caption", 0, 10, 3)

st.markdown('<h3 class="section">2 · Add your photo</h3>', unsafe_allow_html=True)
photo = st.file_uploader(
    "Photo", type=["png", "jpg", "jpeg", "webp"],
    help="Your photo is analyzed in memory and never stored.",
    label_visibility="collapsed",
)

if photo is not None:
    st.image(photo, caption="Preview", use_container_width=True)
else:
    # Empty-state: quick "how it works" strip.
    st.markdown(
        """
        <div class="steps">
          <div class="step"><div class="n">📸</div><div class="t">Upload</div>
            <div class="d">Drop in any photo</div></div>
          <div class="step"><div class="n">🎨</div><div class="t">Pick a vibe</div>
            <div class="d">Six moods to match</div></div>
          <div class="step"><div class="n">✨</div><div class="t">Get captions</div>
            <div class="d">Post-ready + hashtags</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        st.markdown(
            f'<h3 class="section">{VIBE_EMOJI.get(tone, "")} {tone} captions</h3>',
            unsafe_allow_html=True,
        )
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
            copy_text = cap.get("text", "")
            tags = " ".join(cap.get("hashtags", []))
            with st.expander("📋 Copy"):
                st.code(copy_text if not tags else f"{copy_text}\n\n{tags}", language=None)

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="foot">Made with ✨ · '
    '<a href="https://github.com/fayeeza-shaikh/instaptly">source on GitHub</a> · '
    "photos are never stored</div>",
    unsafe_allow_html=True,
)
