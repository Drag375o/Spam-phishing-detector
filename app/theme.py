"""Theme: full-bleed background image, glass cards.

Two Streamlit constraints worth knowing, both learned the hard way:

1. You cannot wrap Streamlit widgets in your own <div>. A widget rendered
   after st.markdown('<div>') becomes a sibling of that div, not a child.
   Every card here is a real st.container(border=True), styled through
   Streamlit's own test-id selector.

2. Streamlit's markdown wrapper is a flex column, so `margin: 0 auto` on
   a max-width block does not reliably centre it. Use a full-width
   wrapper with text-align:center and make the inner element
   display:inline-block instead.

Background: put your image at assets/bg.jpg (preferred), bg.webp, or
bg.png. Target 3840px wide. Use JPEG or WebP — the file is base64-encoded
into the CSS, so a multi-megabyte PNG makes every rerun slow.
"""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# JPEG/WebP first: this gets inlined into the page, so size matters.
CANDIDATES = [
    ("bg.jpg",  "image/jpeg"),
    ("bg.jpeg", "image/jpeg"),
    ("bg.webp", "image/webp"),
    ("bg.png",  "image/png"),
]


def _bg_layer() -> str:
    for name, mime in CANDIDATES:
        p = ASSETS / name
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            return f"url('data:{mime};base64,{b64}')"
    # fallback so the app still runs before you add an image
    return "linear-gradient(160deg,#1B2735 0%,#22303F 45%,#2E4053 100%)"


def css() -> str:
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300..600;1,6..72,300..600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {{
  --serif:'Newsreader',Georgia,serif;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
  --alert:#E86A6A; --caution:#E0A93F; --clear:#5FCFAE;
}}


#MainMenu, footer {{ visibility:hidden; height:0%; }}
header, header[data-testid="stHeader"] {{ visibility:hidden; height:0%; }}
div[data-testid="stToolbar"],
div[data-testid="stToolbarActions"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"] {{
  visibility:hidden !important; height:0% !important; position:fixed !important;
}}


/* ---- background ---- */
.stApp {{
  background:
    linear-gradient(180deg, rgba(12,18,26,.60) 0%, rgba(12,18,26,.44) 45%, rgba(12,18,26,.76) 100%),
    {_bg_layer()};
  background-size:cover, cover;
  background-position:center, center;
  background-attachment:fixed, fixed;
}}

/* wider than default so the masthead sits near the viewport edge and the
   analyzer's two halves get real room */
.block-container {{
  max-width:1560px;
  padding:1.6rem clamp(1.2rem,3vw,3rem) 4rem !important;
}}

/* ---- type ---- */
/* Do not target every `span`: Streamlit uses spans for Material icons, and
   forcing the serif font makes icon names such as `keyboard_arrow_right`
   appear as text. */
.stApp, .stApp p, .stApp div, .stApp label {{ font-family:var(--serif); }}

/* masthead, left aligned */
.brand {{
  font-family:var(--mono); font-size:.76rem; letter-spacing:.08em;
  color:rgba(255,255,255,.72); text-align:left; margin-bottom:11vh;
  /* break out of the centred container to sit at the viewport edge */
  margin-left:calc(50% - 50vw + 2.2rem);
}}
.brand b {{ color:#fff; font-weight:500; }}

/* centred hero block. `.mid` is full width and centres its inline-block
   child — margin:auto is unreliable inside Streamlit's flex wrapper. */
.mid {{ width:100%; text-align:center; }}
.mid > * {{ display:inline-block; text-align:center; }}

.kicker {{
  font-family:var(--mono); font-size:.78rem; letter-spacing:.14em;
  color:rgba(255,255,255,.68); margin:0 0 .9rem;
}}
h1.title {{
  font-family:var(--serif); font-weight:300;
  font-size:clamp(2.8rem,7vw,5.8rem); line-height:.98;
  letter-spacing:-.025em; color:#fff; margin:0 0 1.3rem;
  text-shadow:0 2px 30px rgba(0,0,0,.4);
}}
h1.title i {{ font-weight:400; }}
.lede {{
  max-width:54ch; font-size:1.06rem; line-height:1.66;
  color:rgba(255,255,255,.88); margin:0 0 2.4rem;
  text-shadow:0 1px 16px rgba(0,0,0,.35);
}}
.footnote {{
  font-family:var(--mono); font-size:.73rem; letter-spacing:.04em;
  color:rgba(255,255,255,.6); margin-top:9vh; line-height:1.9;
}}
.panel-title {{
  font-family:var(--mono); font-size:.73rem; letter-spacing:.12em;
  color:rgba(255,255,255,.8); margin-bottom:.6rem;
}}

/* ---- glass cards: real Streamlit containers ---- */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  background:rgba(255,255,255,.10);
  backdrop-filter:blur(22px) saturate(1.3);
  -webkit-backdrop-filter:blur(22px) saturate(1.3);
  border:1px solid rgba(255,255,255,.22) !important;
  border-radius:16px;
  padding:1.5rem 1.6rem !important;
  box-shadow:0 18px 50px -20px rgba(0,0,0,.5);
  animation:rise .55s cubic-bezier(.16,.84,.3,1) both;
}}
@keyframes rise {{
  from {{ opacity:0; transform:translateY(14px); }}
  to   {{ opacity:1; transform:none; }}
}}

div[data-testid="stVerticalBlockBorderWrapper"] p,
div[data-testid="stVerticalBlockBorderWrapper"] div,
div[data-testid="stVerticalBlockBorderWrapper"] span,
div[data-testid="stVerticalBlockBorderWrapper"] label,
div[data-testid="stVerticalBlockBorderWrapper"] td,
div[data-testid="stVerticalBlockBorderWrapper"] th {{
  color:rgba(255,255,255,.9);
}}

.verdict {{
  font-family:var(--serif); font-weight:300;
  font-size:clamp(1.7rem,3.6vw,2.4rem); line-height:1.08;
  letter-spacing:-.02em; margin:.2rem 0 1rem;
}}
.row {{
  display:flex; justify-content:space-between;
  border-top:1px solid rgba(255,255,255,.16);
  padding:.62rem 0; font-family:var(--mono); font-size:.79rem;
  color:rgba(255,255,255,.72);
}}
.row b {{ color:#fff; font-weight:500; }}
.sign {{
  font-family:var(--mono); font-size:.79rem; line-height:1.55;
  border-left:2px solid rgba(255,255,255,.3);
  padding:.42rem 0 .42rem .75rem; margin-bottom:.4rem;
  color:rgba(255,255,255,.85);
}}
.idle {{
  font-family:var(--mono); font-size:.79rem; line-height:1.7;
  color:rgba(255,255,255,.6); text-align:center;
  border:1px dashed rgba(255,255,255,.24);
  border-radius:8px; padding:3rem 1rem;
}}
.small {{
  font-family:var(--mono); font-size:.72rem; line-height:1.65;
  color:rgba(255,255,255,.62);
  border-top:1px solid rgba(255,255,255,.16);
  padding-top:.85rem; margin-top:1.1rem;
}}

/* ---- controls ---- */
/* Streamlit 1.63 puts the textarea surface on this wrapper, not on the
   textarea itself. Give it the same muted glass surface as the expander. */
div[data-testid="stTextAreaRootElement"],
.stSelectbox div:has(> input),
.stSelectbox div[data-baseweb="select"] > div {{
  background:rgba(255,255,255,.08) !important;
  backdrop-filter:blur(12px) saturate(1.3) !important;
  -webkit-backdrop-filter:blur(12px) saturate(1.3) !important;
  border:1px solid rgba(255,255,255,.22) !important;
  border-radius:10px !important;
}}
.stTextArea textarea {{
  font-family:var(--mono) !important; font-size:.84rem !important;
  line-height:1.65 !important;
  background:transparent !important;
  border:none !important;
  border-radius:10px !important; color:#fff !important;
}}
.stTextArea textarea::placeholder {{ color:rgba(255,255,255,.45) !important; }}

.stSelectbox input {{
  background:transparent !important;
  color:#fff !important;
  font-family:var(--mono) !important; font-size:.81rem !important;
}}

.stButton > button {{
  font-family:var(--mono) !important; font-size:.81rem !important;
  letter-spacing:.06em; border-radius:999px !important;
  border:1px solid rgba(255,255,255,.45) !important;
  background:rgba(255,255,255,.12) !important;
  backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  color:#fff !important; padding:.7rem 1.6rem !important;
  transition:background .2s ease, border-color .2s ease, color .2s ease;
}}
.stButton > button:hover {{
  background:rgba(255,255,255,.92) !important;
  border-color:#fff !important; color:#16202B !important;
}}
.stButton > button:focus-visible {{ outline:2px solid #E0A93F; outline-offset:3px; }}

/* Keep the expander's header unchanged when opened, hovered, or pressed.
   Streamlit applies a light `bgMix` color to an open header by default. */
div[data-testid="stExpander"] details {{
  background:rgba(255,255,255,.08) !important;
  border:1px solid rgba(255,255,255,.18) !important;
  border-radius:12px !important;
}}
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] details[open] > summary,
div[data-testid="stExpander"] summary:hover,
div[data-testid="stExpander"] summary:focus-visible,
div[data-testid="stExpander"] summary:active {{
  background:transparent !important;
  box-shadow:none !important;
}}
div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
  background:transparent !important;
}}
div[data-testid="stExpander"] p,
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] td,
div[data-testid="stExpander"] th {{ color:rgba(255,255,255,.85) !important; }}

/* ---- mobile: recompose ---- */
@media (max-width:760px) {{

  .brand {{ margin-bottom:6vh; margin-left:0; }}
  .block-container {{ padding:1.2rem 1rem 3rem !important; }}
  .brand {{ margin-bottom:6vh; }}
  .footnote {{ margin-top:5vh; }}
  .lede {{ font-size:.98rem; }}
  .stApp {{ background-attachment:scroll, scroll; }}
}}

@media (prefers-reduced-motion:reduce) {{
  div[data-testid="stVerticalBlockBorderWrapper"] {{ animation:none; }}
  * {{ transition:none !important; }}
}}
</style>
"""
