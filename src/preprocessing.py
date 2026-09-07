import re

ENTITY_PAT = re.compile(
    r"\b("
    r"enron|hpl|ect|hou|kaminski|vince|shirley|sally|louise|tony|"
    r"cnn|cnncom|lllp|warner|"
    r"python|pythondev|python3000|opensuse|perl|zope|"
    r"ierant|josemonkeyorg|monkeyorg|"
    r"linguistics|uai"
    r")\b", re.I)

URLBLOB_PAT = re.compile(r"\bhttp\w{12,}\b", re.I)
YEAR_PAT    = re.compile(r"\b(19|20)\d{2}\b")
TZ_PAT      = re.compile(r"\b[+-]?0[0-9]{3}\b")
LONGNUM_PAT = re.compile(r"\b\d{4,}\b")
NUM_PAT     = re.compile(r"\b\d+\b")


def normalize(t: str) -> str:
    """Apply the exact text normalisation the model was trained on.

    Order matters: long URLs before their digits are consumed, years
    before generic long numbers.
    """
    t = str(t).lower()
    t = URLBLOB_PAT.sub(" urltoken ", t)
    t = ENTITY_PAT.sub(" enttoken ", t)
    t = YEAR_PAT.sub(" yeartoken ", t)
    t = TZ_PAT.sub(" tztoken ", t)
    t = LONGNUM_PAT.sub(" numtoken ", t)
    t = NUM_PAT.sub(" num ", t)
    return re.sub(r"\s+", " ", t).strip()