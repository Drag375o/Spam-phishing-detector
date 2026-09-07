# Spam & Phishing Email Detector

An NLP and machine-learning system for detecting spam and potentially
phishing-related emails based on textual and structural patterns.

**Test performance: 0.9939 accuracy / 0.9942 F1 on a stratified random split.
On leave-one-corpus-out evaluation, where the test emails come from a source
the model never trained on, accuracy falls to a 0.56–0.99 range (mean 0.865).**

Both numbers are reported because the gap between them is the most useful
thing this project measured. The first says how well the model learned this
dataset; the second is the honest estimate of what happens on unfamiliar mail.

---

## Overview

Paste an email, get a verdict, a model confidence score, a risk level, and a
list of the structural warning signs present in the text.

The prediction comes from a classifier trained on 65,657 emails. The warning
signs come from separate hand-written rules. These two things are deliberately
kept apart in both the code and the interface — the rules explain and adjust
the risk level, but they never change what the model predicted.

No LLM, no external API. The classifier is trained from scratch with
scikit-learn.

## Problem statement

Phishing differs from ordinary spam in an important way: it *imitates*
legitimate mail. Promotional spam has its own vocabulary and is comparatively
easy to separate. A credential-harvesting email is written to look exactly
like a real security notice, which means the two are often textually
identical. This project quantifies how far a text classifier can get, and
where it stops.

## Dataset

[Kaggle — Phishing Email Dataset](https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset)
(not committed; ~250 MB). 82,486 emails merged from six corpora:

| Corpus | Emails | Spam % |
|---|---:|---:|
| CEAS 2008 | 39,154 | 55.8 |
| Enron | 29,767 | 47.0 |
| SpamAssassin | 5,809 | 29.6 |
| Nigerian Fraud | 3,332 | 100.0 |
| Ling | 2,859 | 16.0 |
| Nazario | 1,565 | 100.0 |

After cleaning: **82,072 emails, 52.2% spam / 47.8% ham.**

### A finding that shaped every later decision

The published merged file has already been preprocessed by its authors —
lowercased, punctuation stripped, stopwords removed. Measured directly:

| Signal | Present in |
|---|---:|
| Capital letters | 0.0% |
| `!` and `?` | 0.0% |
| Periods / commas | 0.0% |
| `http` | 47.2% |
| Digits | 94.2% |

So URL *presence* is learnable, but URL structure, casing and punctuation are
not. This is why the structural indicators (uppercase ratio, exclamation
count, IP-address links) are implemented as predict-time rules rather than
trained features — they cannot be learned from text that no longer contains
them, but they *can* be read from a real email pasted into the app.

## Project architecture

```
raw pasted email
      │
      ├──→ normalize() ──→ TF-IDF ──→ classifier ──→ probability   [LEARNED]
      │
      └──→ indicators() ──────────────────────────→ warning list   [NOT LEARNED]
                                    ↓
                          combined risk assessment
```

```
Spam-phishing-detector/
├── data/raw/              # dataset (gitignored)
├── data/processed/        # cleaned.csv
├── notebooks/
│   └── 01_exploration.ipynb
├── src/
│   ├── preprocessing.py   # normalize() — must match training exactly
│   ├── features.py        # indicators() — rule-based, not learned
│   └── predict.py         # loads artifacts, runs assessment
├── models/
│   ├── model.pkl
│   ├── vectorizer_word.pkl
│   ├── vectorizer_char.pkl
│   └── feature_config.json
├── app/app.py             # Streamlit interface
├── results/               # metrics, plots, RESULTS.md
└── requirements.txt
```

`normalize()` and `indicators()` live in `src/` and are imported by both the
notebook and the app, so the two provably cannot drift apart. A notebook
assertion checks this.

## Technologies

Python · pandas · NumPy · scikit-learn · SciPy sparse · Matplotlib · Streamlit
· joblib

## Data preprocessing

414 rows removed from 82,486 (0.5%), each for a stated reason:

- **408 duplicates.** Identical text in both train and test inflates the test
  score — the model would be scored on memorisation.
- **1 blank row.** Produces an all-zero TF-IDF vector.
- **3 single-word rows.** One token carries no usable signal.
- **2 parsing artifacts.** A 107,710-word mailbox file and a 46,425-word
  address dump, neither of which is an email. A genuine 23,359-word Enron news
  digest was checked and kept.

Very short emails were **kept** after verifying they are class-balanced
(376 spam / 369 ham under 10 words), so length alone is not a spam signal at
the low end.

## Exploratory analysis

Median length differs sharply by class: **ham 106 words, spam 55.** Both
distributions are heavily right-skewed (ham mean 204, spam mean 121), so
medians are reported rather than means.

Word-frequency comparison by document rate and smoothed lift surfaced a
problem discussed below.

## Feature engineering

TF-IDF over **word 1–2 grams + character 3–5 grams** (`char_wb`), 453,409
features, `sublinear_tf=True`, `min_df` 5 and 10.

The matrix is **0.134% dense** — as a dense array it would be ~36 GB; stored
sparse it is a few hundred MB. This sparsity is also why linear and
Naive-Bayes models are appropriate and why Random Forest was deliberately not
trained: a tree split on a feature that is zero in 99.87% of rows is close to
useless.

Character n-grams improved F1 from 0.9924 to 0.9950, with the gain
concentrated in **precision** (0.9906 → 0.9941) — fewer legitimate emails
wrongly flagged. Bigrams appear to be doing most of the work: `verify account`
is far more discriminative than `verify` and `account` separately, since
business mail uses "account" constantly.

## Models

Eleven configurations were trained and evaluated on the identical test set.

| Model | Accuracy | Precision | Recall | F1 | Train (s) |
|---|---:|---:|---:|---:|---:|
| Naive Bayes (words) | 0.9776 | 0.9873 | 0.9697 | 0.9784 | 0.03 |
| Naive Bayes (blocklist) | 0.9774 | 0.9869 | 0.9695 | 0.9782 | 0.02 |
| LogReg C=1 (words) | 0.9878 | 0.9839 | 0.9928 | 0.9883 | 1.45 |
| LogReg C=1 (blocklist) | 0.9864 | 0.9833 | 0.9907 | 0.9870 | 1.29 |
| LinearSVC (words) | 0.9928 | 0.9909 | 0.9953 | 0.9931 | 0.34 |
| LinearSVC (blocklist) | 0.9920 | 0.9906 | 0.9942 | 0.9924 | 0.31 |
| LogReg C=1 (n-grams) | 0.9914 | 0.9895 | 0.9940 | 0.9918 | 20.79 |
| LogReg C=5 (n-grams) | 0.9934 | 0.9921 | 0.9953 | 0.9937 | 25.36 |
| LogReg C=20 (n-grams) | 0.9941 | 0.9931 | 0.9956 | 0.9943 | 31.07 |
| LinearSVC (n-grams) | 0.9948 | 0.9941 | 0.9959 | 0.9950 | 3.02 |
| **SGD modified_huber (n-grams)** | **0.9949** | 0.9937 | **0.9966** | **0.9952** | **1.18** |

### Why `SGDClassifier(loss='modified_huber')`

LinearSVC was the strongest of the conventional choices but has no
`predict_proba` — it returns a signed distance from the boundary, not a
probability, and the application needs a confidence score. `modified_huber` is
an SVM-family loss that *does* support `predict_proba`, so it resolves the
tradeoff rather than compromising on it: best F1 in the comparison, native
probabilities, and 1.2 s to train.

The LogReg `C` sweep (0.9918 → 0.9937 → 0.9943) shows regularisation strength
explains part of the SVM advantage but not all of it — LogReg never caught up
even at C=20 and 31 seconds.

Why SGDClassifier ?
> `SGDClassifier` is not fully deterministic across fits even with a fixed
> `random_state`, so the shipped model's metrics (Evaluation section below)
> differ marginally from this comparison run.


## Evaluation

Shipped model, random 80/20 stratified split, seed 42:

| Metric | Value |
|---|---:|
| Accuracy | 0.9939 |
| Precision | 0.9929 |
| Recall | 0.9954 |
| F1 | 0.9942 |
| ROC-AUC | 0.9994 |
| PR-AUC | 0.9993 |

Confusion matrix: **7,786 TN · 61 FP · 39 FN · 8,529 TP**

- **False positive** = a legitimate email sent to spam. Costly to the user; a
  job offer never gets read.
- **False negative** = phishing delivered as safe. Costly to security; the
  user may enter credentials.

Recall is weighted more heavily here because a missed phishing email can cost
an account, while a quarantined newsletter costs an inconvenience. The model
already leans that way (recall 0.9954 > precision 0.9929).

### Generalisation: leave-one-corpus-out

Train on five corpora, test on the sixth. This removes the source overlap that
a random split permits, and it is the number that actually matters.

| Held out | n | Spam % | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| CEAS | 39,154 | 55.8 | 0.8718 | 0.9248 | 0.8385 | 0.8795 |
| Enron | 29,767 | 47.0 | 0.8846 | 0.8400 | 0.9315 | 0.8834 |
| Ling | 2,859 | 16.0 | 0.9409 | 0.7504 | 0.9454 | 0.8367 |
| Nazario | 1,565 | 100.0 | 0.5642 | — | 0.5642 | — |
| Nigerian Fraud | 3,332 | 100.0 | 0.9889 | — | 0.9889 | — |
| SpamAssassin | 5,808 | 29.6 | 0.9384 | 0.8854 | 0.9091 | 0.8971 |

Precision and F1 are omitted for the two 100%-spam corpora, where they are
not meaningful.

Three things follow:

1. **Nazario, a dedicated phishing corpus, is the worst case at 0.564
   recall.** Nearly half of it is missed. Phishing language does not transfer
   from general spam — it is a distinct problem, not a subset.
2. **Nigerian advance-fee fraud generalises well (0.989)** because its
   vocabulary is unmistakable: beneficiary, next of kin, transfer, barrister.
3. **Holding out Enron or Ling collapses precision (0.840, 0.750), not
   recall.** The model's idea of "legitimate" is narrow; unfamiliar genuine
   mail gets flagged.

## Error analysis

All 83 errors from the random split were inspected by hand.

### Error rate by length

| Words | n | Errors | Rate |
|---|---:|---:|---:|
| 0–10 | 114 | 12 | 10.53% |
| 10–25 | 1,746 | 15 | 0.86% |
| 25–100 | 7,538 | 20 | 0.27% |
| 100–500 | 6,250 | 32 | 0.51% |
| 500+ | 767 | 4 | 0.52% |

A 39× difference between the worst and best buckets. The curve is U-shaped:
too little text gives nothing to work with, and very long emails mix quoted
threads, newsletters and unparsed payloads. **The app warns the user when
input is under 10 words.**

### Failure patterns

1. **Label noise.** Several false negatives are ordinary personal
   correspondence labelled spam — a discussion of Medicare coverage for a
   spouse's blood-pressure medication; a complaint about a mailing-list
   moderator. The model called them ham at ~0.000 probability. It was right;
   the labels are wrong.
2. **Legitimate transactional mail is textually identical to phishing.** A
   genuine Citibank registration email was flagged at 1.000 confidence. It
   contains account language, a sign-in URL and statement references —
   precisely what phishing imitates.
3. **Commercial bulk mail sits on the class boundary.** A sales-lead marketing
   email labelled ham reads as promotional spam; annotators would disagree.
4. **Unparsed MIME/base64 payloads** survive in some rows.

A meaningful share of the 83 errors reflect label noise or genuine ambiguity,
so accuracy on this dataset has a practical ceiling below 100%.

## Explainability, and a leakage investigation

Inspecting the linear coefficients produced the most important finding in the
project.

The strongest **ham** features were not language. Nine of the top eleven were
the string `enron` or character fragments of it (`nron`, ` enro`, `enr`),
alongside Enron employee names — `vince`, `sally`, `tony`. The strongest
**spam** features were four-digit years and timezone offsets: `2004`, `2016`,
`0000`, `0300`. The spam corpora were collected later than Enron (2001), so
**the model had learned to read the timestamp.**

Three removal attempts followed:

| Attempt | Result |
|---|---|
| 61-term vocabulary blocklist | −0.0002 F1 |
| Text-level entity + date normalisation | −0.0010 F1 |
| Placeholder tokens (`enttoken`, `yeartoken`) | placeholder became the new top ham feature (−1.898) |

Each attempt removed its targets and each cost ≈0.001 F1. The conclusion is
that corpus identity is carried by **writing register** — `wrote`, `thanks`,
`let know`, `calendar`, `employees` — which no regex can remove. `wrote` is
the single strongest ham feature (−2.032) and it is simply the quoted-reply
marker of threaded human conversation.

**Feature importance shows what a model uses; ablation shows what it needs.
Here the two answers differed,** and the ablation is the better test of
whether leakage matters. The leakage-controlled model is the one shipped.

A caution on reading feature weights: a high spam weight on `verify` does not
mean every email containing "verify" is phishing. The weight says that, all
else equal, the feature shifts the balance. Classification sums hundreds of
them, and plenty of legitimate mail says "verify" — the Citibank false
positive is exactly that.

## Streamlit demo

```
Verdict            Suspicious — treat as unsafe
Risk level         HIGH
Model confidence   99.0%
Length             34 words

Warning signs found in the text
  Contains 1 link(s)
  Link uses a raw IP address instead of a domain
  Urgency language: urgent, immediately, within 24 hours
  Credential/verification request: verify your account, confirm your identity
  Shouted words in capitals: URGENT, NOW
  Excessive exclamation marks (4)
```

Displayed confidence is capped at 99%. `modified_huber` probabilities saturate
at the tails and returned exactly 100.0% on the phishing example, which would
be overclaiming.

## Example predictions on unseen modern email

Nine hand-written cases in categories absent from the training data.

| Case | Truth | Predicted | Confidence | Result |
|---|---|---|---:|---|
| Work reminder | ham | ham | 24.6% | correct |
| Delivery notification | ham | **spam** | 76.7% | **false positive** |
| Bank transaction alert | ham | **spam** | 99.0% | **false positive** |
| GitHub notification | ham | ham | 24.7% | correct |
| Promotional blast | spam | spam | 67.5% | correct |
| Crypto investment | spam | spam | 84.2% | correct |
| Credential phishing | spam | spam | 99.0% | correct |
| Invoice fraud | spam | spam | 99.0% | correct |
| CEO fraud | spam | spam | 89.7% | correct |

**7/9.** Both failures are false positives on legitimate automated mail. All
five spam and phishing cases were caught, including business email compromise
(invoice fraud, CEO fraud) which contains no URLs and no spam vocabulary — a
better result than expected, since nothing resembling BEC is in the training
data.

This confirms the leave-one-corpus-out finding from a third angle. The
model's ham is 2001-era corporate threads and academic mailing lists, so
modern transactional email — banks, shipping, SaaS notifications — is
under-represented and gets flagged.

## Limitations

- Trained on 2001–2008 corpora. Email conventions have changed.
- **Cannot distinguish genuine financial or security mail from a convincing
  forgery**, because the two are textually identical. Demonstrated three
  separate times in this project.
- Casing, punctuation and URL structure are unavailable to the model because
  the published dataset removed them.
- The rule-based indicators are hand-written heuristics, not learned, and can
  false-positive on ordinary text.
- The dataset is 52/48 balanced; a real inbox is far more skewed, so
  thresholds would need recalibrating.
- **Not a security product.** It cannot confirm that an email is safe.

## Future improvements

- Train on a modern corpus with contemporary transactional mail, which is the
  specific gap the evaluation identified.
- Add sender/header features (SPF, DKIM, display-name mismatch, reply-to
  divergence) — these are the signals that actually separate real bank mail
  from a forgery, and text alone cannot.
- Threshold tuning against an explicit cost ratio for false positives versus
  false negatives.
- Calibration (isotonic or Platt) so the confidence score is a genuine
  probability.

## How to run

```bash
git clone https://github.com/Drag375o/Spam-phishing-detector.git
cd Spam-phishing-detector

python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app/app.py
```

The trained model is committed, so the app runs without retraining.

To reproduce training, download the dataset into `data/raw/` and run
`notebooks/01_exploration.ipynb`.



---

Built by [Drag375o](https://github.com/Drag375o). Dataset from
[Kaggle](https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset).