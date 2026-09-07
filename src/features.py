import re

URL_RE    = re.compile(r'https?://[^\s<>"\']+|www\.[^\s<>"\']+', re.I)
IP_URL    = re.compile(r'https?://(?:\d{1,3}\.){3}\d{1,3}', re.I)
SHORTENER = re.compile(r'\b(bit\.ly|tinyurl|goo\.gl|t\.co|ow\.ly|is\.gd|buff\.ly)\b', re.I)
BARE_URL  = re.compile(
    r'\b(?:[a-z0-9-]+\.)+(?:com|net|org|io|ru|cn|info|biz|co|ly|gl|tk|xyz)'
    r'(?:/[^\s]*)?', re.I)

URGENCY = ["urgent","immediately","act now","expires","within 24 hours",
           "last chance","final notice","suspended","deadline","asap",
           "right away","before it","limited time"]
CREDENTIAL = ["verify your account","confirm your identity","update your password",
              "click here to log","sign in to confirm","validate your account",
              "re-enter your","confirm your details","security alert",
              "unusual activity","account will be closed"]
FINANCIAL = ["bank","payment","invoice","wire transfer","refund","tax",
             "credit card","billing","transaction","beneficiary","funds"]
REWARD = ["winner","won","prize","lottery","reward","congratulations",
          "free gift","claim your","selected"]


def indicators(raw: str) -> dict:
    """Rule-based phishing indicators. NOT part of the trained model."""
    t = str(raw)
    low = t.lower()
    urls = set(URL_RE.findall(t)) | set(BARE_URL.findall(t))
    letters = [c for c in t if c.isalpha()]
    caps_ratio = sum(c.isupper() for c in letters)/len(letters) if letters else 0.0
    shouted = [w for w in re.findall(r'\b[A-Za-z]{3,}\b', t) if w.isupper()]

    def hits(terms): return [w for w in terms if w in low]
    u, c, f, r = hits(URGENCY), hits(CREDENTIAL), hits(FINANCIAL), hits(REWARD)

    found = []
    if urls:                found.append(f"Contains {len(urls)} link(s)")
    if IP_URL.search(t):    found.append("Link uses a raw IP address instead of a domain")
    if SHORTENER.search(t): found.append("Uses a URL shortener (destination hidden)")
    if u: found.append(f"Urgency language: {', '.join(u[:3])}")
    if c: found.append(f"Credential/verification request: {', '.join(c[:3])}")
    if f: found.append(f"Financial terminology: {', '.join(f[:3])}")
    if r: found.append(f"Reward/prize language: {', '.join(r[:3])}")
    if len(shouted) >= 2:
        found.append(f"Shouted words in capitals: {', '.join(shouted[:4])}")
    if t.count("!") >= 3:
        found.append(f"Excessive exclamation marks ({t.count('!')})")

    return {
        "n_urls": len(urls), "has_ip_url": bool(IP_URL.search(t)),
        "has_shortener": bool(SHORTENER.search(t)),
        "n_urgency": len(u), "n_credential": len(c),
        "n_financial": len(f), "n_reward": len(r),
        "caps_ratio": round(caps_ratio, 3), "n_shouted": len(shouted),
        "n_exclaim": t.count("!"), "n_words": len(t.split()),
        "flags": found,
    }