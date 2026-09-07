# Error Analysis

Best model: SGDClassifier(loss='modified_huber') on word 1-2 grams + char 3-5 grams.
Test set: 16,415 emails. 83 errors (54 FP, 29 FN).

## Error rate by email length
0-10 words: 10.53% | 10-25: 0.86% | 25-100: 0.27% | 100-500: 0.51% | 500+: 0.52%
Shortest bucket errs 39x more than the best bucket.

## Failure patterns found by manual inspection

1. **Label noise.** Several false negatives are ordinary personal
   correspondence labelled spam (a discussion of Medicare coverage; a
   complaint about a mailing-list moderator). The model assigned them
   ham with ~0.000 spam probability. These appear to be labelling errors
   in the merged source corpora.

2. **Legitimate transactional mail is textually identical to phishing.**
   A genuine Citibank registration email was flagged spam at 1.000
   confidence: it contains account language, a sign-in URL and statement
   references - exactly what phishing imitates. Text alone cannot
   separate real bank mail from a convincing forgery.

3. **Commercial bulk mail sits on the class boundary.** A sales-lead
   marketing email labelled ham reads as promotional spam. Reasonable
   annotators would disagree.

4. **Unparsed MIME/base64 content.** Some emails retain multipart
   headers and encoded payloads instead of readable body text.

5. **Very short emails carry insufficient signal** (see length table).

## Implication
A meaningful share of the 83 errors reflect label noise or genuine
ambiguity rather than model deficiency, so accuracy on this dataset has
a practical ceiling below 100%.
