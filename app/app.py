import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.predict import load_artifacts, assess

st.set_page_config(page_title="Email Risk Analysis", page_icon="🛡️",
                   layout="wide", initial_sidebar_state="collapsed")

INK, PAPER, RULE = "#16202B", "#F7F8FA", "#DDE2E8"
ALERT, CLEAR, CAUTION = "#B4232A", "#1F6F5C", "#B07B18"

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400&display=swap');
html, body, [class*="css"] {{ font-family:'IBM Plex Sans',sans-serif; }}
.block-container {{ padding-top:2.2rem; max-width:1400px; }}
textarea {{ font-family:'IBM Plex Mono',monospace !important; font-size:13px !important; line-height:1.55 !important; }}
h1 {{ font-size:1.45rem !important; font-weight:600 !important; letter-spacing:-.01em; margin-bottom:.15rem !important; }}
.sub {{ color:#5A6672; font-size:.86rem; line-height:1.5; margin-bottom:1.6rem; max-width:62ch; }}
.verdict {{ border:1px solid {RULE}; border-left-width:5px; background:#fff; padding:1.1rem 1.2rem; margin-bottom:1rem; }}
.verdict .label {{ font-size:.74rem; color:#5A6672; margin-bottom:.3rem; }}
.verdict .call {{ font-size:1.3rem; font-weight:600; line-height:1.25; }}
.stat {{ display:flex; justify-content:space-between; border-bottom:1px solid {RULE}; padding:.55rem 0; font-size:.88rem; }}
.stat span:last-child {{ font-weight:600; }}
.ind {{ border-left:3px solid {RULE}; padding:.45rem 0 .45rem .7rem; margin-bottom:.35rem; font-size:.86rem; line-height:1.45; }}
.empty {{ border:1px dashed {RULE}; padding:2.6rem 1.2rem; text-align:center; color:#8A949E; font-size:.88rem; }}
.note {{ background:#fff; border:1px solid {RULE}; padding:.8rem .9rem; font-size:.79rem; color:#5A6672; line-height:1.5; margin-top:1rem; }}
</style>""", unsafe_allow_html=True)


@st.cache_resource
def get_artifacts():
    return load_artifacts()

model, w_vec, c_vec, cfg = get_artifacts()

EXAMPLES = {
    "Paste your own": "",
    "Phishing": ("URGENT: Your account has been suspended!\n\n"
                 "Verify your account immediately at http://192.168.1.50/secure-login "
                 "or it will be closed within 24 hours. Confirm your identity NOW!!!"),
    "Spam": ("CONGRATULATIONS!!! You have WON a $1000 gift card!\n\n"
             "Claim your prize now at bit.ly/x7a9 - limited time only!"),
    "Legitimate": ("Hi team,\n\nMoving tomorrow's standup to 10:30. Agenda and "
                   "notes are in the shared drive.\n\nThanks,\nSam"),
}

st.markdown("# Email risk analysis")
st.markdown('<div class="sub">Classifies email text as spam/phishing-related or '
            'legitimate using a model trained on 65,657 messages, then lists the '
            'structural warning signs found in the text. It cannot confirm that an '
            'email is safe.</div>', unsafe_allow_html=True)

left, right = st.columns([5, 4], gap="large")

with left:
    choice = st.radio("Sample", list(EXAMPLES), horizontal=True,
                      label_visibility="collapsed")
    text = st.text_area("Email", value=EXAMPLES[choice], height=340,
                        placeholder="Paste the email, including subject line...",
                        label_visibility="collapsed")
    go = st.button("Analyze", type="primary", use_container_width=True)

if go and text.strip():
    st.session_state["r"] = assess(text, model, w_vec, c_vec)
elif go:
    st.session_state["r"] = None

with right:
    r = st.session_state.get("r")

    if r is None:
        st.markdown('<div class="empty">Paste an email and select Analyze.</div>',
                    unsafe_allow_html=True)
    else:
        spam = r["raw_proba"] >= 0.5
        colour = {"HIGH": ALERT, "MEDIUM-HIGH": ALERT, "MEDIUM": CAUTION,
                  "LOW-MEDIUM": CAUTION, "LOW": CLEAR}[r["risk"]]
        call = "Suspicious — treat as unsafe" if spam else "No strong signs of spam"

        st.markdown(
            f'<div class="verdict" style="border-left-color:{colour}">'
            f'<div class="label">Verdict</div>'
            f'<div class="call" style="color:{colour}">{call}</div></div>',
            unsafe_allow_html=True)

        st.markdown(
            f'<div class="stat"><span>Risk level</span>'
            f'<span style="color:{colour}">{r["risk"]}</span></div>'
            f'<div class="stat"><span>Model confidence it is spam</span>'
            f'<span>{r["ml_confidence"]}%</span></div>'
            f'<div class="stat"><span>Length</span>'
            f'<span>{r["n_words"]} words</span></div>',
            unsafe_allow_html=True)

        st.progress(r["raw_proba"])

        if r["short_input_warning"]:
            st.warning(f"Only {r['n_words']} words. Emails under 10 words had a "
                       "10.5% error rate in testing, against 0.27% at 25–100 words.")

        st.markdown("###### Warning signs found in the text")
        if r["indicators"]:
            for f in r["indicators"]:
                st.markdown(f'<div class="ind" style="border-left-color:{colour}">'
                            f'{f}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="ind">None of the rule checks triggered.</div>',
                        unsafe_allow_html=True)

        st.markdown('<div class="note"><b>Reading this correctly.</b> The verdict and '
                    'confidence come from the trained classifier. The warning signs '
                    'are separate hand-written checks — they explain the result and '
                    'adjust the risk level, but they do not change what the model '
                    'predicted.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Model")
    st.markdown(f"""
SGDClassifier, modified_huber loss.
{cfg['n_features']:,} features — word 1–2 grams and character 3–5 grams, TF-IDF.
Trained on {cfg['n_train']:,} emails, tested on {cfg['n_test']:,}.

**Random split**
Accuracy {cfg['random_split_metrics']['accuracy']:.4f} · Recall {cfg['random_split_metrics']['recall']:.4f} · F1 {cfg['random_split_metrics']['f1']:.4f}

**Leave-one-corpus-out**
56%–99% accuracy, mean 86.5%%. Held-out-source performance is the honest estimate;
the random-split numbers are optimistic because training and test emails come
from the same six corpora.
""")