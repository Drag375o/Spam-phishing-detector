import json
from pathlib import Path
import joblib
from scipy.sparse import hstack

from .preprocessing import normalize
from .features import indicators

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"


def load_artifacts():
    return (
        joblib.load(MODELS / "model.pkl"),
        joblib.load(MODELS / "vectorizer_word.pkl"),
        joblib.load(MODELS / "vectorizer_char.pkl"),
        json.loads((MODELS / "feature_config.json").read_text()),
    )


def assess(raw_text, model, w_vec, c_vec):
    ind = indicators(raw_text)

    norm = normalize(raw_text)
    X = hstack([w_vec.transform([norm]), c_vec.transform([norm])]).tocsr()
    proba = float(model.predict_proba(X)[0, 1])

    pred = "SPAM / PHISHING-RELATED" if proba >= 0.5 else "LIKELY LEGITIMATE"

    weight = (2*ind["has_ip_url"] + 2*ind["has_shortener"]
              + min(ind["n_credential"], 3) + min(ind["n_urgency"], 2)
              + min(ind["n_reward"], 2))

    if proba >= 0.90:   risk = "HIGH"
    elif proba >= 0.65: risk = "MEDIUM-HIGH" if weight >= 3 else "MEDIUM"
    elif proba >= 0.35: risk = "MEDIUM" if weight >= 4 else "LOW-MEDIUM"
    else:               risk = "LOW-MEDIUM" if weight >= 5 else "LOW"

    # modified_huber saturates at the tails; don't display false certainty
    shown = min(round(100*proba, 1), 99.0)

    return {
        "prediction": pred,
        "ml_confidence": shown,
        "raw_proba": proba,
        "risk": risk,
        "indicators": ind["flags"],
        "n_words": ind["n_words"],
        "short_input_warning": ind["n_words"] < 10,
        "indicator_weight": weight,
    }