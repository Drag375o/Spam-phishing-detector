"""Lottie loading animation from assets/loading.json.

st.markdown strips <script>, so this goes through components.html, which
runs in an iframe where scripts execute. The iframe body is forced
transparent so the animation floats over the background image.
"""
import json
from pathlib import Path

import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
LOTTIE = ROOT / "assets" / "loading.json"

CDN = "https://cdnjs.cloudflare.com/ajax/libs/bodymovin/5.12.2/lottie.min.js"


def lottie(height: int = 180, label: str = "Loading the model"):
    """Render the animation. Silently does nothing if the file is missing."""
    if not LOTTIE.exists():
        return
    data = json.loads(LOTTIE.read_text(encoding="utf-8"))
    components.html(f"""
      <style>
        html,body {{ margin:0; background:transparent; overflow:hidden; }}
        #wrap {{ display:flex; flex-direction:column; align-items:center;
                 justify-content:center; height:{height}px; }}
        #anim {{ width:200px; height:110px; }}
        #cap  {{ font-family:'IBM Plex Mono',ui-monospace,monospace;
                 font-size:11px; letter-spacing:.12em;
                 color:rgba(255,255,255,.7); margin-top:2px; }}
      </style>
      <div id="wrap">
        <div id="anim"></div>
        <div id="cap">{label}</div>
      </div>
      <script src="{CDN}"></script>
      <script>
        lottie.loadAnimation({{
          container: document.getElementById('anim'),
          renderer: 'svg', loop: true, autoplay: true,
          animationData: {json.dumps(data)}
        }});
      </script>
    """, height=height)