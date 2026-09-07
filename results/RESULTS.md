# Results

## Dataset
82,486 emails from the Kaggle Phishing Email Dataset (Enron, Ling, CEAS,
Nazario, Nigerian Fraud, SpamAssassin). After cleaning: **82,072** emails,
52.2% spam / 47.8% ham. Removed 408 duplicates, 1 blank, 3 single-word rows
and 2 parsing artifacts (unparsed mailbox files of 46k and 108k words).
Very short emails were kept after confirming they are class-balanced
(376 spam / 369 ham under 10 words), so length alone is not a spam signal.

The published merged file is already lowercased, stripped of punctuation and
stopword-filtered. Capitals, `!` and `?` are absent (0.0%); `http` survives in
47.2% of emails and digits in 94.2%. URL *presence* is therefore learnable but
URL structure, casing and punctuation are not.

## Final model
`SGDClassifier(loss='modified_huber', alpha=1e-5)` on 453,409 TF-IDF features
(word 1–2 grams + character 3–5 grams, `sublinear_tf`). Trained on 65,657
emails in 1.2 s. `modified_huber` was chosen because it is the only
SVM-family loss in scikit-learn that supports `predict_proba`, which the
application needs for a confidence score.

## Random-split performance (80/20 stratified, seed 42)
| Metric | Value |
|---|---|
| Accuracy | 0.9939 |
| Precision | 0.9929 |
| Recall | 0.9954 |
| F1 | 0.9942 |
| ROC-AUC | 0.9994 |
| PR-AUC | 0.9993 |

Confusion matrix: 7,786 TN · 61 FP · 39 FN · 8,529 TP.

## Model comparison
| model                            |   accuracy |   precision |   recall |     f1 |   train_s |
|:---------------------------------|-----------:|------------:|---------:|-------:|----------:|
| NB (A: with artifacts)           |     0.9776 |      0.9873 |   0.9697 | 0.9784 |      0.03 |
| NB (B: artifacts removed)        |     0.9774 |      0.9869 |   0.9695 | 0.9782 |      0.02 |
| LogReg (A)                       |     0.9878 |      0.9839 |   0.9928 | 0.9883 |      1.45 |
| LogReg (B)                       |     0.9864 |      0.9833 |   0.9907 | 0.987  |      1.29 |
| LinearSVC (A)                    |     0.9928 |      0.9909 |   0.9953 | 0.9931 |      0.34 |
| LinearSVC (B)                    |     0.992  |      0.9906 |   0.9942 | 0.9924 |      0.31 |
| LinearSVC (C: word+char n-grams) |     0.9948 |      0.9941 |   0.9959 | 0.995  |      3.02 |
| LogReg C=1.0 (n-grams)           |     0.9914 |      0.9895 |   0.994  | 0.9918 |     20.79 |
| LogReg C=5.0 (n-grams)           |     0.9934 |      0.9921 |   0.9953 | 0.9937 |     25.36 |
| LogReg C=20.0 (n-grams)          |     0.9941 |      0.9931 |   0.9956 | 0.9943 |     31.07 |
| SGD modified_huber (n-grams)     |     0.9949 |      0.9937 |   0.9966 | 0.9952 |      1.18 |

Each feature-set upgrade gave a real gain: word unigrams 0.9924 → word+char
n-grams 0.9950 (F1), with the improvement concentrated in **precision**
(0.9906 → 0.9941), i.e. fewer legitimate emails wrongly flagged.

## Generalisation: leave-one-corpus-out
Training on five corpora and testing on the sixth. This is the honest
estimate, because it removes the source overlap a random split allows.

| held_out     |   n_test |   test_spam_pct |   accuracy |   precision |   recall |       f1 |
|:-------------|---------:|----------------:|-----------:|------------:|---------:|---------:|
| CEAS         |    39154 |            55.8 |     0.8718 |      0.9248 |   0.8385 |   0.8795 |
| Enron        |    29767 |            47   |     0.8846 |      0.84   |   0.9315 |   0.8834 |
| Ling         |     2859 |            16   |     0.9409 |      0.7504 |   0.9454 |   0.8367 |
| Nazario      |     1565 |           100   |     0.5642 |    nan      |   0.5642 | nan      |
| Nigerian     |     3332 |           100   |     0.9889 |    nan      |   0.9889 | nan      |
| SpamAssassin |     5808 |            29.6 |     0.9384 |      0.8854 |   0.9091 |   0.8971 |

Accuracy falls from 0.9939 to a 0.56–0.99 range (mean ≈0.88). Nazario — a
dedicated phishing corpus — is the worst case at 0.564 recall: **phishing
language does not transfer from general spam**. Nigerian advance-fee fraud
generalises well (0.989) because its vocabulary is highly distinctive.
Holding out Enron or Ling collapses *precision* (0.840, 0.750) rather than
recall, showing the model's notion of "legitimate" is narrow.

## Error analysis
| bucket   |    n |   errors |   error_rate_pct |
|:---------|-----:|---------:|-----------------:|
| 0-10     |  114 |       12 |            10.53 |
| 10-25    | 1746 |       15 |             0.86 |
| 25-100   | 7538 |       20 |             0.27 |
| 100-500  | 6250 |       32 |             0.51 |
| 500+     |  767 |        4 |             0.52 |

Emails under 10 words err at 10.53% against 0.27% at 25–100 words — a 39×
difference. The application warns the user when input is under 10 words.

Manual inspection of all 83 errors found:
1. **Label noise.** Several false negatives are ordinary personal
   correspondence labelled spam (a discussion of Medicare coverage; a
   mailing-list complaint), assigned ham at ~0.000 probability.
2. **Legitimate transactional mail is textually identical to phishing.** A
   genuine Citibank registration email was flagged at 1.000 confidence.
3. **Commercial bulk mail sits on the class boundary** and would be labelled
   inconsistently by human annotators.
4. **Unparsed MIME/base64 payloads** remain in some rows.

A meaningful share of the errors reflect label noise or genuine ambiguity, so
accuracy on this dataset has a practical ceiling below 100%.

## Leakage investigation
Inspecting the linear coefficients showed the model's strongest features were
corpus artifacts, not language: nine of the top eleven ham features were the
string "enron" or character fragments of it, alongside Enron employee names
(`vince`, `sally`, `tony`); the strongest spam features were four-digit years
and timezone offsets (`2004`, `2016`, `0000`, `0300`) — the model was reading
timestamps, because the spam corpora were collected later than Enron (2001).

Three removal attempts were made: a 61-term vocabulary blocklist, text-level
entity and date normalisation, and placeholder substitution. Each removed the
targeted features and each cost ≈0.001 F1 (0.9952 → 0.9942). Placeholder
tokens simply became the new leak (`enttoken` at −1.898). The conclusion is
that corpus identity is carried by writing register — `wrote`, `thanks`,
`let know`, `calendar`, `employees` — which cannot be removed by feature
surgery. **Feature importance shows what a model uses; ablation shows what it
needs. Here the answer differed.** The leakage-controlled model is the one
shipped.

## Unseen modern email
Nine hand-written cases in categories absent from the training data.

| case          | truth   | predicted   |   conf | risk   |   n_flags | correct   |
|:--------------|:--------|:------------|-------:|:-------|----------:|:----------|
| work_reminder | ham     | ham         |   24.6 | LOW    |         0 | True      |
| delivery      | ham     | spam        |   76.7 | MEDIUM |         1 | False     |
| real_bank     | ham     | spam        |   99   | HIGH   |         1 | False     |
| github        | ham     | ham         |   24.7 | LOW    |         1 | True      |
| promo         | spam    | spam        |   67.5 | MEDIUM |         4 | True      |
| crypto        | spam    | spam        |   84.2 | MEDIUM |         0 | True      |
| credential    | spam    | spam        |   99   | HIGH   |         3 | True      |
| invoice_fraud | spam    | spam        |   99   | HIGH   |         1 | True      |
| ceo_fraud     | spam    | spam        |   89.7 | MEDIUM |         2 | True      |

7/9 correct. Both failures are **false positives on legitimate automated
mail**: a genuine bank transaction alert (flagged at 99%) and a shipping
confirmation (76.7%). All five spam/phishing cases were caught, including
business email compromise (invoice fraud, CEO fraud) which contains no URLs
or spam vocabulary.

This confirms the leave-one-corpus-out finding from a third angle: the model's
ham is 2001-era corporate threads and academic mailing lists, so modern
transactional email — banks, shipping, SaaS notifications — is
under-represented and gets flagged.

## Limitations
- Trained on 2001–2008 corpora; email conventions have changed.
- Cannot distinguish genuine financial/security mail from a convincing
  forgery, because the two are textually identical.
- Casing, punctuation and URL structure are unavailable to the model because
  the published dataset removed them.
- The rule-based indicators are hand-written heuristics, not learned, and
  can false-positive.
- Not a security product. It cannot confirm that an email is safe.
