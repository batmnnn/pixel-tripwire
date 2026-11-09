# Deviations from PRD v9

## D1 — Own encoders (owner decision, 7 November 2026, 16:50 IST)

PRD v9: "No encoder creation." Changed to: build scripted SASH-style encoders for four scheme classes from the public class-level descriptions.

Reason: no licensed positive examples were available, and without them the study had no recall or defense measurement.

Guards:
- Encoders are frozen before detectors are written.
- Detectors are calibrated on development data only.
- A held-out variant B tests generalization.
- The study is described as a synthetic benchmark, not a SASH replication.
- Encoder code and positive images stay private.

The same author writes the encoders and the detectors. The report discloses this as a bias toward known classes.

## D2 — Sample size (16:55 IST)

PRD v9 targeted 48 base images. Changed to 48 development and 96 held-out.

Reason: synthetic generation costs nothing, and per-class intervals at n=9 would be uninformative.

## D3 — Receiver model (16:55 IST)

PRD v9 named the 2.2B SmolVLM2 as the fallback. Changed to the 500M SmolVLM2.

Reason: the 2.2B model needs about 9 GB of F32 weights. This machine has 8 GB of RAM and 12 GB of free disk. The Modal account has not been checked.

## D5 — Draw order of the LINE chart (17:20 IST)

After F1, the reference decoder misread some dashed lines because the solid series line was drawn on top and split dashes. Changed `pt/charts.py` to draw the dashed target line above the series. No detector code existed yet. Development images were regenerated, and F1 was re-frozen as F1b.

Reference decoder fidelity after the fix, on throwaway seeds that are not dev or held-out: 959 of 960 images exact (120 per carrier and variant). The one miss was LINE variant B. Development: 24 of 24.

## D4 — Added arms (16:55 IST)

Added the REF reference decoder and the R2 canonicalization arm. REF is needed because a tool-free receiver may recover nothing, which would leave the defense unmeasured. R2 is secondary.

## D6: Where and when the primary receiver ran (9 November 2026)

The pre-registered T, V and R arms (SmolVLM2-500M, F2 prompts and parser, hash-checked at start) ran after the non-VLM held-out results were already known. Nothing in the prompts, parser or model changed. The first local run on Apple MPS was killed by memory pressure after 29 outputs. All 576 jobs were then rerun on two Azure CPU VMs (Standard_D48s_v5, fp32, greedy decoding), split into 12 shards. The 29 local MPS answers match the Azure CPU answers exactly, 29 of 29 (`runs/vlm_backend_check.json`).

## D7: Secondary receiver (not pre-registered)

The 500M receiver read all titles but recovered nothing, and it flagged images by chart type. To test whether a capable open model behaves differently, we ran Qwen2.5-VL-7B-Instruct (Apache-2.0, revision cc594898) on the same frozen prompts, images and parser. The plan was a Modal GPU, but Modal requires a payment method for any GPU, so the run moved to five Azure CPU VMs (fp32). This analysis was decided after the primary results were seen, and the report labels it secondary.

## D8: Exploratory analyses (after the results)

- `private/exploratory_grid.py`: a label-anchored GRID reader, used to test whether the frozen decoder's 0/12 under jitter reflects the defense or the decoder.
- `private/exploratory_partial.py`: position-wise character agreement, to measure partial leakage that exact match hides.

Neither changes any frozen result. Both are reported as exploratory.

## D9: Replication split (after all frozen results, 9 November)

- A fresh split of 384 images, made with `private/build_rep.py` (seed MASTER_SEED+300). It uses the frozen generator, encoders, detectors, thresholds and defenses without changes. Words are reused about twice each.
- Rendering ran on the original Mac. Scoring ran on an Azure VM with Tesseract 5.5.1 and the Mac's tessdata and dictionary.
- A parity check against the 96 frozen held-out results matched all 96 scores, flags and decoder outputs.

## D10: Monitor stress tests (after all frozen results, 9 November)

- **Hinted monitor prompt.** The frozen MONITOR prompt plus one sentence naming the four public scheme classes, saved in `private/monitor_hint_prompt.txt`. The reply format and parser are unchanged.
- **Qwen2.5-VL-32B-Instruct** (revision 7cfb30d7, Apache-2.0), run on held-out originals with both the generic and the hinted prompt.
- **Overt positive control.** 24 clean held-out charts with a visible note to Agent B naming a code word, scored by both Qwen models with both prompts. This tests whether a "no" from a monitor means anything.

## D11 — Threshold-free statistics (post-freeze, exploratory)
- **Added on 9 Nov 2026, 16:10 IST, after all results:** `private/exploratory_stats.py`, which writes `runs/exploratory_stats.json`.
- **What it computes:**
  - Per-carrier AUROC for each carrier's own detector, with 5,000-resample bootstrap intervals. Each carrier's negatives are its own clean images.
  - Fisher exact tests on counts already reported.
- **Inputs:** frozen scores and frozen thresholds only. Nothing was refit.
- **Findings:**
  - GRID AUROC is at chance (0.54 held-out, 0.49 replication).
  - BAR variant B AUROC is 0.25: every variant B chart scores 0, tied with half the clean charts.
  - The variant A/B recall gap on replication is significant (p = 2.3e-6).
- Reported in Appendix C of the report.
