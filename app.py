"""
Instaptly — a photo-first Instagram caption generator (prototype)
-------------------------------------------------------------------
Pure-Python Flask app. Upload a photo, pick a vibe, get captions.

Palette: "Sunset Pop"  (#FF5E62 / #FF9966 / #FFD166 / #2B2D42 / #FFF3EC)

HOW IT WORKS
  * By default it returns fun MOCK captions so you can click the whole
    flow with no API key and no cost.
  * To make it real, set an ANTHROPIC_API_KEY env var and flip
    USE_REAL_AI = True below. The photo is sent to the model in-memory
    and never written to disk (see generate_captions_ai).

RUN
  pip install flask
  python app.py
  # open http://127.0.0.1:5000
"""

import base64
import random
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
USE_REAL_AI = True             # flip to True once you add an API key
ANTHROPIC_MODEL = "claude-sonnet-5"
MAX_UPLOAD_MB = 10

TONES = ["Funny", "Aesthetic", "Minimal", "Bold", "Inspirational", "Story"]

# ---------------------------------------------------------------------------
# MOCK CAPTION BANK  (used when USE_REAL_AI is False)
# ---------------------------------------------------------------------------
MOCK = {
    "Funny": [
        "I put the 'pro' in procrastinate 😎",
        "Warning: may contain traces of main character energy.",
        "Not me pretending this was candid 📸",
        "My hobbies include this exact pose.",
    ],
    "Aesthetic": [
        "golden hour, golden mood ☀️",
        "soft light, softer thoughts.",
        "collecting moments, not things ✨",
        "a little poetry in every frame.",
    ],
    "Minimal": [
        "here.",
        "mood 🤍",
        "just this.",
        "unbothered.",
    ],
    "Bold": [
        "out here glowing and I know it ⚡️",
        "confidence level: selfie with no filter.",
        "main character. no notes. 💅",
        "the moment chose me.",
    ],
    "Inspirational": [
        "Grow through what you go through 🌱",
        "Small steps still move you forward.",
        "Be the energy you want to attract.",
        "Your only limit is you — so go.",
    ],
    "Story": [
        "Woke up, chased the light, found this little moment worth keeping. 🌅",
        "Some days ask for nothing but presence — this was one of them.",
        "Between the plans and the pauses, here's where the magic snuck in.",
        "It started as an ordinary day and somehow became a favorite.",
    ],
}

HASHTAGS = {
    "Funny": ["#lol", "#relatable", "#justvibes", "#nofilterneeded"],
    "Aesthetic": ["#aesthetic", "#goldenhour", "#moodygrams", "#softlife"],
    "Minimal": ["#minimal", "#lessismore", "#mood", "#simple"],
    "Bold": ["#maincharacter", "#confidence", "#slay", "#glowup"],
    "Inspirational": ["#growth", "#mindset", "#dailymotivation", "#goodvibes"],
    "Story": ["#storytime", "#momentslikethese", "#everydaymagic", "#slowliving"],
}


def generate_captions_mock(tone, n=5, tags_per_caption=3):
    pool = MOCK.get(tone, MOCK["Aesthetic"])
    caps = (pool * ((n // len(pool)) + 1))[:n]
    random.shuffle(caps)
    tag_pool = HASHTAGS.get(tone, [])
    out = []
    for c in caps:
        k = min(tags_per_caption, len(tag_pool))
        out.append({"text": c, "hashtags": random.sample(tag_pool, k=k) if k else []})
    return out


def generate_captions_ai(image_bytes, mime, tone, n=5, tags_per_caption=5):
    """Real generation. Image stays in memory — never written to disk.

    The model returns each caption together with its own reach-optimized
    hashtag set: a mix of broad high-volume tags + a few niche tags that
    are easier to rank in. Output is structured JSON so hashtags come back
    clean, no fragile line-parsing.
    """
    import os
    import json
    import re
    import anthropic  # pip install anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    prompt = (
        f"You are an Instagram caption + hashtag expert. Look at this photo and "
        f"write {n} '{tone}'-style captions. Each caption must be short and "
        f"post-ready.\n\n"
        f"For EACH caption also generate {tags_per_caption} relevant hashtags, "
        f"chosen for reach: mix 2 broad/high-volume tags with a few smaller "
        f"niche tags that are easier to rank in. No spaces, each starts with '#'.\n\n"
        f"Respond with ONLY a JSON array, no prose, in exactly this shape:\n"
        f'[{{"text": "the caption", "hashtags": ["#tag1", "#tag2"]}}]'
    )

    msg = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=900,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64",
                                              "media_type": mime, "data": b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )

    # The model may return thinking blocks before the text; grab the text block.
    raw = "".join(
        block.text for block in msg.content if getattr(block, "type", None) == "text"
    ).strip()
    return _parse_ai_captions(raw, n, tags_per_caption)


def _parse_ai_captions(raw, n=5, tags_per_caption=5):
    """Robustly pull captions + hashtags out of the model's reply.

    Tries strict JSON first; if the model wrapped it in prose or code fences,
    falls back to extracting the JSON array, then finally to line-parsing.
    """
    import json
    import re

    def _clean_tags(tags):
        out = []
        for t in tags or []:
            t = str(t).strip()
            if not t:
                continue
            t = "#" + re.sub(r"[^0-9A-Za-z_]", "", t.lstrip("#"))
            if len(t) > 1:
                out.append(t)
        return out[:tags_per_caption]

    # 1) direct JSON, or JSON hidden inside code fences / surrounding text
    candidate = raw
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if m:
        candidate = m.group(0)
    try:
        data = json.loads(candidate)
        captions = []
        for item in data[:n]:
            if isinstance(item, dict) and item.get("text"):
                captions.append({
                    "text": str(item["text"]).strip(),
                    "hashtags": _clean_tags(item.get("hashtags")),
                })
        if captions:
            return captions
    except (json.JSONDecodeError, TypeError):
        pass

    # 2) fallback: split lines, separate any inline #hashtags from the caption
    captions = []
    for line in raw.splitlines():
        line = line.strip(" .0123456789)-*").strip()
        if not line:
            continue
        tags = _clean_tags(re.findall(r"#\w+", line))
        text = re.sub(r"#\w+", "", line).strip(" ,-–")
        if text:
            captions.append({"text": text, "hashtags": tags})
        if len(captions) >= n:
            break
    return captions


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template_string(PAGE, tones=TONES)


@app.route("/generate", methods=["POST"])
def generate():
    tone = request.form.get("tone", "Aesthetic")
    try:
        tags_per = int(request.form.get("tags", 3))
    except (TypeError, ValueError):
        tags_per = 3
    tags_per = max(0, min(tags_per, 10))   # clamp to a sane range

    file = request.files.get("photo")
    if not file:
        return jsonify({"error": "No photo uploaded"}), 400

    if USE_REAL_AI:
        image_bytes = file.read()          # in memory only
        if len(image_bytes) > MAX_UPLOAD_MB * 1024 * 1024:
            return jsonify({"error": "Image too large"}), 400
        captions = generate_captions_ai(image_bytes, file.mimetype, tone,
                                        tags_per_caption=tags_per)
        # image_bytes goes out of scope here — nothing is stored
    else:
        captions = generate_captions_mock(tone, tags_per_caption=tags_per)

    return jsonify({"tone": tone, "captions": captions})


# ---------------------------------------------------------------------------
# FRONTEND  (Sunset Pop palette)
# ---------------------------------------------------------------------------
PAGE = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Instaptly</title>
<style>
  :root{
    --coral:#FF5E62; --peach:#FF9966; --gold:#FFD166;
    --ink:#2B2D42; --cream:#FFF3EC;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,sans-serif;
       background:var(--cream);color:var(--ink);min-height:100vh}
  .wrap{max-width:520px;margin:0 auto;padding:28px 18px 60px}
  h1{font-size:30px;margin:0 0 2px;font-weight:800;
     background:linear-gradient(90deg,var(--coral),var(--peach));
     -webkit-background-clip:text;background-clip:text;color:transparent}
  .sub{opacity:.65;margin:0 0 22px;font-size:14px}
  .card{background:#fff;border-radius:18px;padding:18px;
        box-shadow:0 6px 24px rgba(43,45,66,.08)}
  .drop{display:flex;flex-direction:column;align-items:center;justify-content:center;
        width:100%;min-height:180px;box-sizing:border-box;
        border:2px dashed var(--peach);border-radius:14px;padding:26px;
        text-align:center;cursor:pointer;transition:.15s;background:#fff9f5}
  .drop:hover{background:#fff3ec;border-color:var(--coral)}
  .drop.has{min-height:0;padding:8px}
  .drop img{max-width:100%;max-height:230px;border-radius:10px;display:block;margin:0 auto}
  .drop .hint{font-size:14px;opacity:.7}
  .drop .emoji{font-size:34px;line-height:1;margin-bottom:8px}
  .label{font-size:12px;font-weight:700;text-transform:uppercase;
         letter-spacing:.5px;opacity:.6;margin:20px 0 8px}
  .tones{display:flex;flex-wrap:wrap;gap:8px}
  .tone{border:1px solid #ffd9c7;background:#fff;color:var(--ink);
        padding:7px 14px;border-radius:20px;font-size:13px;cursor:pointer;transition:.12s}
  .tone.active{background:var(--gold);border-color:var(--gold);font-weight:700}
  .gen{width:100%;margin-top:22px;border:0;border-radius:12px;padding:14px;
       font-size:16px;font-weight:800;color:#fff;cursor:pointer;
       background:linear-gradient(90deg,var(--coral),var(--peach));transition:.15s}
  .gen:hover{filter:brightness(1.05)}
  .gen:disabled{opacity:.5;cursor:not-allowed}
  .results{margin-top:22px;display:flex;flex-direction:column;gap:10px}
  .cap{background:#fff;border-radius:12px;padding:13px 14px;
       box-shadow:0 3px 12px rgba(43,45,66,.06);display:flex;
       justify-content:space-between;align-items:flex-start;gap:10px}
  .cap p{margin:0;font-size:15px;line-height:1.4}
  .cap .tags{font-size:12px;color:var(--coral);margin-top:5px;display:block}
  .copybtns{display:flex;flex-direction:column;gap:6px}
  .copy{border:0;background:var(--cream);color:var(--ink);border-radius:8px;
        padding:6px 10px;font-size:12px;font-weight:700;cursor:pointer;white-space:nowrap}
  .copy:hover{background:var(--gold)}
  .copy.alt{background:#fff;border:1px solid #ffd9c7}
  .spin{text-align:center;padding:16px;opacity:.6;font-size:14px}
  .slabel{display:flex;justify-content:space-between;align-items:center}
  .slabel .val{color:var(--coral);font-weight:800}
  input[type=range]{width:100%;accent-color:var(--coral);margin-top:4px}
</style>
</head>
<body>
<div class="wrap">
  <h1>Instaptly ✨</h1>
  <p class="sub">Upload a pic, get a caption that sounds like you.</p>

  <div class="card">
    <label class="drop" id="drop">
      <span class="emoji">📸</span>
      <span class="hint">Tap to upload a photo</span>
      <input id="file" type="file" accept="image/*" hidden>
    </label>

    <div class="label">Pick a vibe</div>
    <div class="tones" id="tones">
      {% for t in tones %}
      <button class="tone {% if loop.first %}active{% endif %}" data-tone="{{t}}">{{t}}</button>
      {% endfor %}
    </div>

    <div class="label slabel">
      <span>Hashtags per caption</span><span class="val" id="tagVal">3</span>
    </div>
    <input type="range" id="tagRange" min="0" max="10" value="3">

    <button class="gen" id="gen" disabled>✨ Generate captions</button>
  </div>

  <div class="results" id="results"></div>
</div>

<script>
const fileInput=document.getElementById('file');
const drop=document.getElementById('drop');
const gen=document.getElementById('gen');
const results=document.getElementById('results');
let currentTone="{{tones[0]}}", currentFile=null;

const tagRange=document.getElementById('tagRange');
const tagVal=document.getElementById('tagVal');
tagRange.addEventListener('input',()=>{tagVal.textContent=tagRange.value;});

drop.addEventListener('click',()=>fileInput.click());
fileInput.addEventListener('change',e=>{
  const f=e.target.files[0]; if(!f)return;
  currentFile=f; gen.disabled=false;
  const url=URL.createObjectURL(f);
  drop.classList.add('has');
  drop.innerHTML='<img src="'+url+'">';
});

document.getElementById('tones').addEventListener('click',e=>{
  if(!e.target.classList.contains('tone'))return;
  document.querySelectorAll('.tone').forEach(b=>b.classList.remove('active'));
  e.target.classList.add('active');
  currentTone=e.target.dataset.tone;
});

gen.addEventListener('click',async()=>{
  if(!currentFile)return;
  results.innerHTML='<div class="spin">Cooking up captions… 🍳</div>';
  const fd=new FormData();
  fd.append('photo',currentFile);
  fd.append('tone',currentTone);
  fd.append('tags',tagRange.value);
  const r=await fetch('/generate',{method:'POST',body:fd});
  const data=await r.json();
  results.innerHTML='';
  (data.captions||[]).forEach(c=>{
    const div=document.createElement('div');
    div.className='cap';
    const tags=(c.hashtags||[]).join(' ');

    const info=document.createElement('div');
    info.innerHTML='<p>'+c.text+'</p>'+(tags?'<span class="tags">'+tags+'</span>':'');

    const btns=document.createElement('div');
    btns.className='copybtns';

    const flash=(el,msg)=>{const o=el.textContent;el.textContent=msg;
                           setTimeout(()=>el.textContent=o,1200);};

    const bAll=document.createElement('button');
    bAll.className='copy';
    bAll.textContent='Copy all';
    bAll.addEventListener('click',()=>{
      navigator.clipboard.writeText(c.text+(tags?' '+tags:''));flash(bAll,'Copied!');});
    btns.appendChild(bAll);

    if(tags){
      const bTags=document.createElement('button');
      bTags.className='copy alt';
      bTags.textContent='Tags only';
      bTags.addEventListener('click',()=>{
        navigator.clipboard.writeText(tags);flash(bTags,'Copied!');});
      btns.appendChild(bTags);
    }

    div.appendChild(info);
    div.appendChild(btns);
    results.appendChild(div);
  });
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True, port=5000)
