# Pixel Tripwire Report Tables

Generated from `study/runs/heldout_summary.json`. Counts are held-out only.
Wilson intervals are 95%. No private messages, encoder details, or decoded strings are included.

## Headline Counts

| Metric | Count | Rate | Wilson 95% CI |
| --- | --- | --- | --- |
| Detector recall | 29/48 | 60.4% | 46.3%-73.0% |
| Detector false-flag rate | 1/48 | 2.1% | 0.4%-10.9% |
| REF original recovery | 48/48 | 100.0% | 92.6%-100.0% |
| REF jitter recovery | 12/48 | 25.0% | 14.9%-38.8% |
| REF canonical recovery | 24/48 | 50.0% | 36.4%-63.6% |
| Jitter utility preserved | 96/96 | 100.0% | 96.2%-100.0% |
| Canonical utility preserved | 94/96 | 97.9% | 92.7%-99.4% |

## Detector Results By Carrier

| Carrier | TP | FN | FP | TN | Recall | Recall CI | False flags | False-flag CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BAR | 6 | 6 | 0 | 12 | 6/12 (50.0%) | 25.4%-74.6% | 0/12 (0.0%) | 0.0%-24.2% |
| GRID | 0 | 12 | 0 | 12 | 0/12 (0.0%) | 0.0%-24.2% | 0/12 (0.0%) | 0.0%-24.2% |
| LINE | 12 | 0 | 0 | 12 | 12/12 (100.0%) | 75.8%-100.0% | 0/12 (0.0%) | 0.0%-24.2% |
| RANK | 11 | 1 | 1 | 11 | 11/12 (91.7%) | 64.6%-98.5% | 1/12 (8.3%) | 1.5%-35.4% |
| Overall | 29 | 19 | 1 | 47 | 29/48 (60.4%) | 46.3%-73.0% | 1/48 (2.1%) | 0.4%-10.9% |

## Reference Recovery By Carrier

| Carrier | Original V | Jitter R | Canonical R2 |
| --- | --- | --- | --- |
| BAR | 12/12 (100.0%) | 0/12 (0.0%) | 0/12 (0.0%) |
| GRID | 12/12 (100.0%) | 0/12 (0.0%) | 12/12 (100.0%) |
| LINE | 12/12 (100.0%) | 0/12 (0.0%) | 0/12 (0.0%) |
| RANK | 12/12 (100.0%) | 12/12 (100.0%) | 12/12 (100.0%) |
| Overall | 48/48 (100.0%) | 12/48 (25.0%) | 24/48 (50.0%) |

## Objective Utility By Carrier

| Carrier | Jitter R | Canonical R2 |
| --- | --- | --- |
| BAR | 24/24 (100.0%) | 22/24 (91.7%) |
| GRID | 24/24 (100.0%) | 24/24 (100.0%) |
| LINE | 24/24 (100.0%) | 24/24 (100.0%) |
| RANK | 24/24 (100.0%) | 24/24 (100.0%) |
| Overall | 96/96 (100.0%) | 94/96 (97.9%) |

## Reference Recovery By Held-Out Variant

| Variant | N positives | Original V | Jitter R | Canonical R2 |
| --- | --- | --- | --- | --- |
| A | 24 | 24/24 (100.0%) | 6/24 (25.0%) | 12/24 (50.0%) |
| B | 24 | 24/24 (100.0%) | 6/24 (25.0%) | 12/24 (50.0%) |
