"""Spam & phishing email detector — web interface.

    streamlit run app/app.py

Two screens on one background image:
  landing   title, description, buttons, Analyze in the centre
  analyzer  same background, split in two — email left, results right

Put your image at assets/bg.png. Without it the app falls back to a
gradient rather than crashing.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st

from app.theme import css
from src.predict import load_artifacts, assess

st.set_page_config(page_title="Spam & phishing detector", page_icon="◫",
                   layout="wide", initial_sidebar_state="collapsed")
st.markdown(css(), unsafe_allow_html=True)

st.session_state.setdefault("page", "home")
st.session_state.setdefault("result", None)


@st.cache_resource
def artifacts():
    return load_artifacts()


SAMPLES = {
    "Paste your own": "",
    "Phishing — credential request": (
        "From: security@citlbank.com\n"
        "Subject: Unusual sign-in activity\n\n"
        "We detected a sign-in from an unrecognised device. Verify your "
        "account within 24 hours or access will be suspended.\n\n"
        "Verify now: http://citi-account-verify.tk/login"),
    "Spam — prize offer": (
        "CONGRATULATIONS!!! You have WON a $1000 gift card!\n\n"
        "Claim your prize now at bit.ly/x7a9 — limited time only!"),
    "Legitimate — work email": (
        "Hi team,\n\nMoving tomorrow's standup to 10:30. Agenda and notes "
        "are in the shared drive.\n\nThanks,\nSam"),
}

RISK_COLOUR = {
    "HIGH": "var(--alert)", "MEDIUM-HIGH": "var(--alert)",
    "MEDIUM": "var(--caution)", "LOW-MEDIUM": "var(--caution)",
    "LOW": "var(--clear)",
}


def go(page):
    st.session_state.page = page
    st.rerun()


# ---------------------------------------------------------------- home
def home():
    st.markdown(
        '<div class="brand"><b>Spam / phishing detector</b> &nbsp;·&nbsp; '
        'email forensics</div>', unsafe_allow_html=True)

    st.markdown("""
      <div class="mid"><p class="kicker">phishing works because the fake looks familiar</p></div>
      <div class="mid"><h1 class="title">Can you tell<br><i>which one is real?</i></h1></div>
      <div class="mid"><p class="lede">An NLP and machine-learning system for
      detecting spam and potentially phishing-related emails based on textual
      and structural patterns.</p></div>
    """, unsafe_allow_html=True)

    # Analyze, centred under the title
    _, mid, _ = st.columns([2, 1, 2])
    with mid:
        if st.button("Analyze an email", use_container_width=True):
            go("analyzer")

    # secondary actions
    _, a, b, c, _ = st.columns([1.1, 1, 1, 1, 1.1])
    with a:
        if st.button("How it works", use_container_width=True):
            go("how")
    with b:
        if st.button("The numbers", use_container_width=True):
            go("numbers")
    with c:
        if st.button("Limitations", use_container_width=True):
            go("limits")

    st.markdown("""
      <div class="mid"><div class="footnote">
        trained on 82,072 emails from six corpora &nbsp;·&nbsp; no LLM, no API<br>
        0.9939 accuracy on familiar mail &nbsp;·&nbsp; 0.564 on a phishing
        corpus it had never seen
      </div></div>""", unsafe_allow_html=True)

    

# ------------------------------------------------------------ analyzer
def analyzer():
    from app.loader import lottie

    slot = st.empty()
    with slot.container():
        lottie(label="Loading the model")
    model, w_vec, c_vec, cfg = artifacts()
    slot.empty()

    st.markdown(
        '<div class="brand" style="margin-bottom:1.4rem">'
        '<b>Email analyzer</b> &nbsp;·&nbsp; paste an email, examine the '
        'signals</div>', unsafe_allow_html=True)

    back, _ = st.columns([1, 6])
    with back:
        if st.button("← Home"):
            go("home")

    st.write("")
    left, right = st.columns(2, gap="large")

    # -- left half: the email
    with left:
        st.markdown('<div class="panel-title">EMAIL CONTENT</div>',
                    unsafe_allow_html=True)
        with st.container(border=True):
            pick = st.selectbox("Load a sample", list(SAMPLES),
                                label_visibility="collapsed")
            text = st.text_area(
                "Email text", value=SAMPLES[pick], height=300,
                placeholder="Paste the email text here...",
                label_visibility="collapsed")
            st.markdown(
                f'<div class="row"><span>{len(text.split())} words</span>'
                f'<span>{len(text)} characters</span></div>',
                unsafe_allow_html=True)
            if st.button("Analyze email", use_container_width=True):
                st.session_state.result = (
                    assess(text, model, w_vec, c_vec) if text.strip() else None)

    # -- right half: everything else
    with right:
        st.markdown('<div class="panel-title">VERDICT</div>',
                    unsafe_allow_html=True)
        r = st.session_state.result

        with st.container(border=True):
            if r is None:
                st.markdown(
                    '<div class="idle">Waiting for analysis.<br>'
                    'Paste an email on the left, or load a sample.</div>',
                    unsafe_allow_html=True)
            else:
                spam = r["raw_proba"] >= 0.5
                col = RISK_COLOUR[r["risk"]]
                word = "Spam or phishing" if spam else "No strong signals"

                signs = "".join(f'<div class="sign">{s}</div>'
                                for s in r["indicators"])
                if not signs:
                    signs = ('<div class="sign">No structural signals found '
                             'in the text.</div>')
                if r["short_input_warning"]:
                    signs = (
                        f'<div class="sign" style="border-left-color:'
                        f'var(--caution)">Only {r["n_words"]} words. Emails '
                        f'under ten words were misclassified 10.5% of the '
                        f'time in testing, against 0.27% at 25–100 words.'
                        f'</div>') + signs

                st.markdown(f"""
                  <div class="verdict" style="color:{col}">{word}</div>
                  <div class="row"><span>risk level</span>
                    <b style="color:{col}">{r['risk']}</b></div>
                  <div class="row"><span>model confidence it is spam</span>
                    <b>{r['ml_confidence']}%</b></div>
                  <div class="row"><span>length</span>
                    <b>{r['n_words']} words</b></div>
                  <div class="panel-title" style="margin:1.4rem 0 .6rem">
                    WARNING SIGNS</div>
                  {signs}
                  <div class="small">The verdict and confidence come from the
                  trained classifier. The warning signs are a separate layer
                  of hand-written rule checks — they explain the result and
                  adjust the risk level, but do not change what the model
                  predicted. It cannot confirm that an email is safe.</div>
                """, unsafe_allow_html=True)

        with st.expander("About the model"):
            st.markdown(f"""
`SGDClassifier` with modified Huber loss over **{cfg['n_features']:,}**
TF-IDF features — word 1–2 grams and character 3–5 grams. Trained on
**{cfg['n_train']:,} emails** from six corpora collected 2001–2008.
No LLM, no API.

| | accuracy |
|---|---:|
| familiar mail, random split | 0.9939 |
| held-out-source average | 0.865 |
| unseen phishing corpus | 0.564 |

Confidence is capped at 99% — modified Huber probabilities saturate at the
extremes and are not calibrated there.
""")


# ------------------------------------------------------------ sub-pages
TEXTS = {
    "how": ("How it works", """
Two things happen to an email, and they are kept separate on purpose.

**The classifier.** The text is normalised the same way the training data
was, converted to TF-IDF features over word 1–2 grams and character 3–5
grams, and scored by the trained model. This produces the verdict and the
confidence figure.

**The rule checks.** Separately, the raw text is scanned for structural
signals — links using a raw IP address, URL shorteners, credential-request
phrasing, urgency language, reward language, shouted capitals, excessive
punctuation. These produce the warning signs.

The rules explain the result and can raise the risk level. They never change
what the model predicted. Presenting a regex match as a model detection
would be dishonest, so the interface labels them apart.
"""),
    "numbers": ("The numbers", """
| | value |
|---|---:|
| emails after cleaning | 82,072 |
| source corpora | 6 |
| training set | 65,657 |
| features | 453,409 |
| accuracy, random split | 0.9939 |
| precision | 0.9929 |
| recall | 0.9954 |
| F1 | 0.9942 |
| ROC-AUC | 0.9994 |

Eleven model and feature configurations were compared on the same test set.
`SGDClassifier` with modified Huber loss won — it was the only SVM-family
loss that also produces probabilities, which the confidence figure needs.

**Held out an entire corpus at a time**, accuracy ranged from 0.564 to
0.9889, averaging 0.865. That is the honest estimate. The random-split
figure is optimistic because training and test emails come from the same
six collections.
"""),
    "limits": ("Limitations", """
**It cannot confirm that an email is safe.** It reports patterns associated
with spam and phishing. It cannot verify a sender.

**Genuine financial mail is textually identical to phishing.** Tested on a
real bank transaction alert, the model flagged it at 99% confidence. The
same happened with a genuine Citibank registration email during error
analysis. This is not a bug that better features fix — phishing is a
deliberate imitation of exactly that kind of message.

**The training corpora are from 2001–2008.** The legitimate mail is largely
Enron corporate threads and academic mailing lists, so modern transactional
email — banks, shipping, service notifications — is under-represented and
gets flagged.

**Phishing language does not transfer from general spam.** Held out a
dedicated phishing corpus, recall fell to 0.564.

**The rule checks are heuristics** and can fire on ordinary text.

Not a security product.
"""),
}


def subpage(key):
    title, body = TEXTS[key]
    st.markdown(f'<div class="brand" style="margin-bottom:1.4rem">'
                f'<b>{title}</b></div>', unsafe_allow_html=True)
    back, _ = st.columns([1, 6])
    with back:
        if st.button("← Home"):
            go("home")
    st.write("")
    _, mid, _ = st.columns([0.4, 3, 0.4])
    with mid:
        with st.container(border=True):
            st.markdown(body)


# ----------------------------------------------------------------- route
page = st.session_state.page
if page == "analyzer":
    analyzer()
elif page in TEXTS:
    subpage(page)
else:
    home()