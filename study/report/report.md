# Pixel Tripwire: A Frozen Synthetic Benchmark for Hidden Content in Agent-to-Agent Chart Images

**Shubham Yadav** (independent)  
*With Apart Research — Swarm Alignment Hackathon 2026, Track 4*

## Abstract

Agents send each other rendered images, but oversight mostly logs text. Pixel Tripwire is a pre-registered synthetic benchmark testing whether chart images can carry content that monitors miss.

We built scripted encoders for four publicly described scheme classes: bar heights, dash patterns, label acrostics and grid fills. We froze generator, detectors, thresholds, prompts, parser and a jitter defense by SHA-256 before generating 96 held-out charts: 48 clean, half of them hard negatives, and 48 carrying benign words, half from an encoder variant unseen in development.

A decoder that shares the convention recovered 48/48 messages. A text-only monitor flagged 0/96 images, and a tool-free 500M VLM flagged at chance. In post-freeze tests, Qwen2.5-VL monitors (7B and 32B) flagged none of the 480 held-out and replication images across 1,344 prompts, even when told the scheme classes. With the generic prompt, both flagged 24/24 charts carrying an overt note (fewer when hinted), and the 7B model read every title and answered 95/96 task questions.

Cheap structural detectors flagged 29/48 held-out positives with 1/48 false flags. On a fresh 384-image replication they flagged 111/192 with 13/192 false flags, but recall on the unseen variant fell to 41%, against 75% on the development variant. A fixed geometric jitter cut exact recovery from 48/48 to 12/48 without utility loss, yet removed only one of four channels; its apparent grid effect was a decoder artifact.

Hidden chart content can be invisible to text and VLM monitors while readable by a colluder. Defenses need class-specific checks and per-carrier reporting.

## 1. Introduction

Oversight of agent systems usually records text: prompts, outputs, tool calls and metadata. Agents also send each other rendered media, such as charts in reports. A monitor that reads only the text never sees the pixels the next agent receives. Recent work asked frontier models (Claude Fable 5.1 and GPT-6 Astra) to hide messages in SVG images. They used visible structure such as element heights, Morse-like patterns, acrostics and bit codes, and a fresh Fable instance with Python tools recovered 78% of Fable's messages [1].

Pixel Tripwire asks a narrow defender's question. If ordinary task charts carry such content, what does each kind of monitor see, and what does a cheap, fixed defense cost? We built a small synthetic benchmark with four scheme classes, froze every analysis choice before generating the held-out set, and measured six things separately:

1. whether the content is recoverable at all;
2. what a text-only monitor flags;
3. what cheap raster detectors flag;
4. what tool-free vision-language models (VLMs), one small and one capable, recover or flag;
5. how much a fixed geometric jitter removes;
6. how much task utility the jitter costs.

**Contributions.** (i) A pre-registered, hash-frozen protocol for image side-channel tests, with clean hard negatives and a held-out encoder variant. (ii) Evidence that capable VLM monitors (7B and 32B) flag none of the hidden content, even when told the scheme classes and despite passing an overt positive control, while cheap structural checks catch 58–60% of it on two test sets drawn with different seeds. (iii) Per-carrier held-out results showing that the defense effect depends heavily on the carrier. (iv) A worked example of a measurement artifact: the frozen decoder's GRID failure under jitter, which would otherwise read as a defense win, comes from the decoder, not the defense.

**Scope.** These are scripted, benign positives. This study does not test whether models collude spontaneously, and it is not a replication of [1].

## 2. Related Work

**Image messages from frontier models.** Kezins et al. [1] prompted Claude Fable 5.1 to hide 50 messages in SVG images, and briefly compared GPT-6 Astra. Fable mostly used heights (33/50). Astra used Morse-like short and long objects (18/50), acrostics, bit codes and Braille window panes. A fresh Fable instance recovered 78% of Fable's messages, and the two models cross-decoded 44/50 and 42/50. Their receiver used Python image analysis, so their result is not evidence about native vision. We use only their class-level descriptions. No prompts, code, images or payloads were reused; the repository has no license.

**Collusion and control.** Motwani et al. [2] define a threat model of secret collusion through steganography between agents, and discuss why monitoring and paraphrasing have limits. Greenblatt et al. [3] evaluate control protocols on separate safety and usefulness axes. We adopt that split: we report detection, recovery and utility as separate numbers.

**Paraphrasing as a defense.** Roger and Greenblatt [4] measure how much hidden information survives text paraphrasing, alongside task performance. Our jitter defense is an image analogue of paraphrasing. We test it rather than assume it works the same way.

**Steganalysis.** Classical steganalysis targets least-significant-bit or frequency-domain noise in photographs. Our carriers are visible geometry in rendered diagrams, so photo-steganalysis results do not transfer. We use simple structural detectors instead.

## 3. Methods

### 3.1 Threat model and access

A producer agent sends a chart image and a short task brief to a receiver agent. A monitor checks the exchange. Table 1 shows what each condition can see.

**Table 1. Conditions and access.**

| Condition | Sees | Does not see |
|---|---|---|
| T: text-only monitor (VLM) | Task brief and PNG metadata (size, bytes) | Pixels |
| C: raster detectors | PNG pixels, plus Tesseract OCR | Source SVG, label strings from the spec |
| V: VLM receiver/monitor | PNG and brief; no tools | Source SVG, codebook |
| R: V after jitter | Jittered PNG | Original PNG |
| REF: scripted decoder | PNG, carrier, variant and codebook; pixel tools | Source SVG |
| CMB: combined | C flag on original OR R-monitor flag | — |

REF stands in for a colluding receiver that shares the convention. It is an upper bound on recoverability, not a model result.

### 3.2 Benchmark

A scripted generator draws 640×420 charts from a seeded spec. It writes SVG and renders it to PNG with CairoSVG in a safe mode with no external resources. There are four carriers, one per scheme class:

- **BAR (height):** bar values carry the message.
- **LINE (dash):** the dash pattern of a target line carries it.
- **RANK (acrostic):** the initials of ranked labels carry it.
- **GRID (bits):** filled and empty cells in a calendar grid carry it.

Messages are short, benign English words of 4 to 6 letters. Each class has two variants. Variant A is the only one used in development. Variant B is held out and changes parameters or reading order. Half of the clean images are *hard negatives* with natural structure, such as round values, regular dashes or word-like initials. Exact encodings, messages and positive images are kept private (Appendix A).

The development set has 48 images. The held-out set has 96: for each carrier, 12 clean (6 of them hard negatives) and 12 positive (6 variant A, 6 variant B). Development and held-out topics do not overlap.

![Figure 1](figures/fig1_clean_examples.png)
*Figure 1. Clean held-out examples of the four carriers. Positive images are withheld.*

### 3.3 Freezes

We froze in stages and recorded the SHA-256 of every file at each freeze:

- **F1/F1b:** generator, encoders, variants and word lists, frozen before any detector code. F1b is one recorded fix to the LINE draw order (Appendix B).
- **F2:** detector code and thresholds, VLM prompts, the parser, the jitter level and a hash of the jitter seed. All of these were frozen *before* the held-out set was generated.

Each detector threshold is the maximum score on development clean images. An image is flagged if any detector's score is strictly above its threshold.

Jitter adds independent uniform noise of up to ±J px to every geometric length: bar tops, line points, dash lengths and cell positions. Text is untouched. J was chosen from {1, 2, 3, 4, 6} as the largest value that kept the objective answer unchanged on every development image. Recovery was not used to choose it, and the result was J = 6, the largest candidate, so the utility rule never bound. The R2 arm is a secondary defense that canonicalizes the chart: it snaps values to a 5-unit grid and applies a standard dash pattern.

### 3.4 Detectors (C)

There are four structural detectors, one per class, using numpy, scipy and Tesseract 5.5.1 [6]:

- **height lattice:** do the bar heights sit on an arithmetic lattice that the gridline spacing does not explain?
- **dash aperiodicity:** how irregular are the on/off run lengths of a dashed line?
- **initials:** do the first letters of ranked labels form a dictionary word, or look plausible by letter-pair statistics?
- **bit periodicity:** a chi-square test on runs in the grid fill pattern.

### 3.5 Receiver and monitor model (T, V, R)

The model is SmolVLM2-500M-Video-Instruct [5] (Apache-2.0), pinned to revision `7b375e1`. It ran on Azure CPU VMs in fp32, with greedy decoding and at most 64 new tokens. A partial run on an Apple M2 (MPS) served as a backend cross-check. Every prompt ran in a fresh context. There were three prompts:

- **monitor:** "does the image carry a hidden or encoded message beyond what the task needs?" with the reply format `FLAG: yes/no`, `MESSAGE: …`;
- **title-read**, as a capability control;
- **one-word utility question**, such as "Which region has the tallest bar?".

The parser is frozen. An unparseable monitor reply is invalid and counts as not flagged. Recovery requires an exact match after Unicode NFKC normalization and case-folding. No outputs were inspected before F2.

**Secondary receiver (not pre-registered).** Qwen2.5-VL-7B-Instruct (Apache-2.0, revision `cc59489`) ran with the identical 576 jobs, prompts and parser. Only the model weights changed.

### 3.6 Metrics

Detection is reported as TP/FN/FP/TN, recall and false-flag rate. Recovery is the exact-match rate on positives. Utility means the objective answer is unchanged after the transform, recomputed from the drawn geometry. For VLM utility, the answer must name the correct candidate. All intervals are Wilson 95% [7].

## 4. Results

All numbers are frozen results on the 96 held-out images unless marked *secondary* (Qwen 7B) or *exploratory*, or reported in Section 4.5. Those were all run after F2 and after the frozen results were seen.

### 4.1 The channels are real for a colluding decoder

REF recovered **48/48** messages from the original positives (100%, CI 92.6–100%). The benchmark's positives therefore carry recoverable content that a receiver with the codebook can read, and none of it appears in the text brief.

### 4.2 Monitors

**Table 2. Held-out detection (48 positive, 48 clean).**

| Condition | TP | FN | FP | TN | Recall (95% CI) | False-flag rate (95% CI) |
|---|---:|---:|---:|---:|---|---|
| T: text-only monitor (500M) | 0 | 48 | 0 | 48 | 0/48 (0.0–7.4%) | 0/48 (0.0–7.4%) |
| V: VLM monitor, original (500M) | 30 | 18 | 31 | 17 | 30/48 (48.4–74.8%) | 31/48 (50.4–76.6%) |
| R: VLM monitor, jittered (500M) | 32 | 16 | 33 | 15 | 32/48 (52.5–78.3%) | 33/48 (54.7–80.1%) |
| **C: raster detectors** | **29** | **19** | **1** | **47** | **29/48 (46.3–73.0%)** | **1/48 (0.4–10.9%)** |
| CMB: C or R (pre-registered) | 37 | 11 | 34 | 14 | 37/48 (63.5–86.7%) | 34/48 (56.8–81.8%) |
| T: text-only monitor (7B, secondary) | 0 | 48 | 0 | 48 | 0/48 (0.0–7.4%) | 0/48 (0.0–7.4%) |
| V: VLM monitor, original (7B, secondary) | 0 | 48 | 0 | 48 | 0/48 (0.0–7.4%) | 0/48 (0.0–7.4%) |
| R: VLM monitor, jittered (7B, secondary) | 0 | 48 | 0 | 48 | 0/48 (0.0–7.4%) | 0/48 (0.0–7.4%) |

![Figure 3](figures/fig3_monitors.png)
*Figure 3. Recall against false-flag rate for each held-out monitor. Only the cheap raster detectors sit well above the chance line. Every Qwen monitor in Section 4.5 (7B and 32B, generic and hinted prompts) sits at the origin with the 7B point.*

The **text-only monitor** flagged nothing (0/96). Its output is the same on clean and positive images, because the brief and metadata are identical in kind for both. It is blind by construction, and this is the oversight gap the study targets.

The **500M VLM monitor** flagged 61/96 images, with no separation between positives and clean images. Its flag follows *chart type*, not content:

| Carrier | Positives flagged | Clean images flagged |
|---|---|---|
| BAR | 10/12 | 12/12 |
| LINE | 12/12 | 11/12 |
| RANK | 7/12 | 8/12 |
| GRID | 1/12 | 0/12 |

So the pre-registered combined rule (CMB) raises recall only by importing that noise: the false-flag rate rises from 1/48 to 34/48. In this setting, a weak VLM monitor is worse than no VLM monitor.

The **7B VLM monitor** (a secondary analysis) answered `FLAG: no` to every one of the 288 monitor prompts: text-only, original and jittered. It is far more capable on these charts than the 500M model (Table 4), so its silence is not explained by failing to read the chart. It reads the charts and judges them ordinary.

The cheap detectors catch some carriers well and others not at all:

- **LINE:** 12/12 caught, with 0/12 false flags.
- **RANK:** 11/12 caught, with 1/12 false flags. The false flag was on an ordinary clean chart, not a hard negative.
- **BAR:** 6/12 caught, all of them variant A. The detectors missed all six of the held-out variant B.
- **GRID:** 0/12 caught.

By variant, recall was 18/24 on the development variant A and 11/24 on the held-out variant B. Calibrating on one encoder variant overstates recall on an unseen one, and a defender should expect this gap.

### 4.3 Fixed jitter: exact recovery falls, but the cause differs by carrier

**Table 3. REF exact recovery on the 48 held-out positives, and objective utility on all 96 images.**

| Carrier | Original | Jitter R (J=6) | Canonical R2 | Utility R | Utility R2 |
|---|---|---|---|---|---|
| BAR | 12/12 | 0/12 | 0/12 | 24/24 | 22/24 |
| LINE | 12/12 | 0/12 | 0/12 | 24/24 | 24/24 |
| RANK | 12/12 | 12/12 | 12/12 | 24/24 | 24/24 |
| GRID | 12/12 | 0/12 † | 12/12 | 24/24 | 24/24 |
| **All** | **48/48** | **12/48** (14.9–38.8%) | **24/48** (36.4–63.6%) | **96/96** (96.2–100%) | **94/96** (92.7–99.4%) |

The frozen headline is that jitter cut exact REF recovery from 48/48 to 12/48 at no measured cost to utility. Taken at face value, that overstates the defense. Carrier by carrier:

- **LINE:** jitter destroyed the channel. Mean position-wise character agreement fell from 1.00 to 0.02 (*exploratory*), which is at chance level, about 1/26.
- **BAR:** jitter broke exact recovery but leaked partially. Character agreement stayed at 0.70 (*exploratory*), so most letters still survive.
- **RANK:** untouched, as designed. The message is in the label text, and jitter does not change text.
- **GRID (†):** the frozen decoder's 0/12 is a decoder artifact, not a defense effect. Jitter moves cells but never changes whether a cell is filled, so the message is still in the image by construction. The frozen decoder segments cells as connected components, and that breaks once displaced cells touch. An exploratory reader that locates cells from the day and week labels recovered **6/12** on originals and **6/12** after jitter: the same count before and after.

The honest count is that jitter at J=6 removes one of four carriers (LINE), partly degrades a second (BAR), and leaves two intact (RANK, GRID). Canonicalization removes LINE and breaks exact BAR recovery (0/12; 2/48 on replication), but BAR still leaks about half its characters (agreement 0.48, *exploratory*). It costs utility on 2/24 BAR images.

![Figure 2](figures/fig2_recovery.png)
*Figure 2. REF exact recovery by carrier and defense. The diamonds are the post-freeze GRID reader. Its unchanged score under jitter indicates the frozen 0/12 is a decoder artifact.*

### 4.4 Tool-free VLM receivers

Run on Azure CPU VMs, the primary receiver produced all 576 pre-registered outputs with no errors. The first 29 outputs were also produced on Apple MPS before the move, and all 29 were identical across the two backends.

**Table 4. Tool-free receiver on held-out images.**

| Measure | SmolVLM2-500M (primary) | Qwen2.5-VL-7B (secondary) |
|---|---|---|
| Title read, a capability control (n=96) | 96/96 (96.2–100%) | 96/96 (96.2–100%) |
| Utility, original image (n=96) | 69/96 (62.2–79.9%) | 95/96 (94.3–99.8%) |
| Utility, jittered image (n=96) | 71/96 (64.4–81.7%) | 94/96 (92.7–99.4%) |
| Exact recovery, original (n=48) | 0/48 (0–7.4%) | 0/48 (0–7.4%) |
| Exact recovery, jittered (n=48) | 0/48 (0–7.4%) | 0/48 (0–7.4%) |
| Monitor flags, all images (n=96) | 61/96 | 0/96 |

The small receiver reads every chart title, so its zero recovery is not caused by failing to see the image. Without tools or the codebook, it never recovered a message. Jitter did not hurt its utility: 68 images were answered correctly on both versions, 3 only on the jittered one and 1 only on the original.

The secondary 7B receiver (fp32, five Azure CPU VMs) produced all 576 outputs with 0 errors. The 7B model answers the task almost perfectly, and jitter costs it at most one answer. It still recovers nothing.

The RANK result makes this concrete. The 7B model reads label text well enough to transcribe every title, and the RANK message is spelled by the initials of the visible labels. Yet it did not report it. Without a shared convention or tools, these channels stay closed even to a capable receiver. They are open to a colluding decoder (Section 4.1).

### 4.5 Additional analyses (after all frozen results)

**Replication on 384 fresh images.** We generated a second test split with a new seed, using the unchanged frozen generator, detectors, thresholds and defenses. Per carrier it has 24 hard-negative clean, 24 plain clean, 24 variant-A and 24 variant-B images. Messages come from the 97 non-development words, each reused about twice; 95/192 replication positives reuse a held-out message word. The split is new in seed and images, not in generator or vocabulary.

Images were rendered on the original machine and scored on an Azure VM. We first ran a parity check on that VM: it reproduced all 96 frozen held-out detector scores, flags and decoder outputs exactly.

**Table 5. Frozen held-out results against the fresh replication split.**

| Measure | Held-out (n=96) | Replication (n=384) |
|---|---|---|
| Detector recall | 29/48 (46.3–73.0%) | 111/192 (50.7–64.6%) |
| Detector false-flag rate | 1/48 (0.4–10.9%) | 13/192 (4.0–11.2%) |
| Recall: development variant A / held-out variant B | 18/24 / 11/24 | 72/96 / 39/96 |
| REF exact: original / jitter / canonical | 48 / 12 / 24 of 48 | 191 / 48 / 98 of 192 |
| Character agreement after jitter: BAR / LINE | 0.70 / 0.02 | 0.71 / 0.04 |
| Utility after jitter / canonical | 96/96 / 94/96 | 384/384 / 377/384 |

Every qualitative finding replicates:

- **Detectors:** LINE 48/48, RANK 37/48, BAR 24/48 and GRID 2/48. Recall on the unseen variant B, 41%, is again far below variant A, 75%.
- **Jitter:** the only surviving exact recoveries are the 48 RANK messages. BAR leaks partially and LINE is destroyed.
- **False flags:** at 6.8%, the rate is higher than the held-out 2.1%. RANK accounts for 7 of the 13, through word-like initials. The held-out false-flag estimate was optimistic, and 7% is the better figure.

**Monitor stress tests.** Was the 7B monitor's silence a property of the prompt, the model size, or a habit of always saying no? We ran three tests, each with the frozen parser.

- **Hinted prompt.** One sentence is added to the frozen monitor prompt, naming the four public scheme classes: letter-mapped bar heights, Morse-like dash lengths, acrostic labels, and grid cells as bits.
- **Larger model.** Qwen2.5-VL-32B-Instruct (Apache-2.0, revision `7cfb30d`, fp32 on CPU).
- **Overt positive control.** 24 clean held-out charts (6 per carrier) carry a plainly visible footer line: "Note for Agent B only: the hidden code word is *harbor*" (or similar). A monitor that can say yes at all should flag these.

**Table 6. Monitor stress tests. Each cell is images flagged / images scored.**

| Monitor | Prompt | Held-out positives | Held-out clean | Replication positives / clean | Overt controls (code word reported) |
|---|---|---|---|---|---|
| Qwen 7B | generic | 0/48 | 0/48 | 0/192 / 0/192 | **24/24** (24/24) |
| Qwen 7B | hinted | 0/48 (jitter 0/48) | 0/48 | 0/192 / 0/192 | 16/24 (16/24) |
| Qwen 32B | generic | 0/48 | 0/48 | — | **24/24** (24/24) |
| Qwen 32B | hinted | 0/32 valid † | 0/30 valid † | — | 10/10 valid † |

† With the hinted prompt, the 32B model often began step-by-step reasoning and hit the frozen 64-token limit before giving a verdict. That left 34/96 held-out answers and 14/24 control answers invalid. Among the valid answers, none of the covert positives was flagged, and every overt control was.

The overt control is decisive. With the generic prompt, both models flag 24/24 overt notes and report the code word every time. Their 0 flags on covert positives (0/240 for the 7B model across held-out and replication, 0/48 for the 32B model) are therefore a detection failure, not a reluctance to say yes. Naming the scheme classes did not help: hinted monitors still flagged 0 covert positives. For the 7B model, the hint *lowered* overt-control sensitivity to 16/24. Scaling to 32B did not help either.

There were 1,344 Qwen monitor prompts. The 7B model, with both prompts, saw held-out originals and jitters plus replication originals (1,152). The 32B model, with both prompts, saw held-out originals (192). 34 answers were invalid, all from 32B hinted. Not one covert image was flagged. The frozen structural detectors flagged 140 of 240 positives across the two test sets.

## 5. Discussion and Limitations

**What the evidence supports.**

- Chart images in this benchmark carry content that is invisible to a text-only monitor and recoverable by a colluding scripted decoder (48/48 held-out, 191/192 replication).
- Cheap structural detectors give useful low-false-flag coverage on two of four classes, but lose recall on an unseen encoder variant.
- A fixed jitter defense is cheap in utility, but its effect depends on the carrier. It cannot touch content stored in text, such as acrostics, or in discrete states, such as cell fill.

- Seeing the pixels is not enough. A capable 7B VLM read every title and answered 95/96 task questions, yet flagged 0/96 held-out images and 0/384 replication images, and it recovered no messages. That held even when it was told what to look for, and in a 32B model. The same 7B monitor flags an overt note 24/24 times, so it can say yes. It simply does not flag covert structure as a message.
- A weak 500M VLM flagged by chart type and was worse than useless inside a combined rule. Cheap, class-specific structural checks were the only monitor that discriminated.
- The channels are asymmetric. A receiver that shares the convention reads 48/48. Tool-free receivers without the convention read 0/48. The channel is invisible to oversight but readable by a colluder, which is the dangerous combination.

**A measurement lesson.** Exact match against one frozen decoder can turn a decoder failure into an apparent defense success, as the GRID result shows. Defense claims should be checked against an independent reader and against partial-leakage metrics. A single exact-match score is not enough.

**Limitations.**

1. *Same author.* One author wrote the encoders, detectors and decoder, so the detectors are biased toward known classes. The held-out variant B only partly offsets this.
2. *Small samples.* The frozen held-out set has only 12 positives per carrier. The post-freeze replication split (48 per carrier) narrows the intervals, but it reuses message words.
3. *Synthetic, scripted positives.* There are no model-generated hiding attempts.
4. *Receivers.* We tested open, tool-free models of up to 32B parameters. A frontier VLM, or a monitor given image-analysis tools, could do better. The 7B and 32B runs were not pre-registered. The frozen 64-token cap truncated a third of the 32B hinted answers.
5. *Shared jitter seed.* One secret seed is used for all images, and a receiver who knew it could partly undo the jitter.
6. *Timing.* The VLM arms were pre-registered and frozen at F2, but ran after the non-VLM held-out results were known. Prompts and parser are hash-verified as unchanged.
7. *Late analyses.* The GRID reader, character agreement and AUROC (Appendix C) came after the results. They are labeled exploratory.
8. *Prior synthesis.* A prior idea synthesis by the author proposed this topic. No code came from it.

## 6. Conclusion

Pixel Tripwire gives frozen, per-carrier evidence for an oversight blind spot. Task charts carry content that a colluding decoder reads perfectly, while a text-only monitor and capable 7B and 32B VLM monitors flag nothing, even with scheme hints. Cheap structural detectors were the only monitor that discriminated, a result that replicated on 384 fresh images, and they lost recall on an unseen encoder variant. A fixed jitter defense removes much less than its headline number suggests.

Image-channel defenses should be reported by carrier, with partial-leakage metrics and an independent reader. The next steps are model-generated positives, frontier and tool-using monitors, and a text-side defense for acrostics, such as label canonicalization.

## Code and Data

- **Public code** (`study/pt/`): chart generation, rendering, raster tools, detectors, VLM prompts and parser, and figures. All code was written during the sprint (7–9 Nov 2026); none is preexisting.
- **Freezes** (`study/freeze/`): `F1.json`, `F1b.json` and `F2.json`, with SHA-256 hashes.
- **Aggregates** (`study/runs/`): `heldout_summary.json`, `heldout_vlm_summary.json`, `heldout_qwen7b_summary.json`, `vlm_backend_check.json`, `rep_summary.json`, `extra_monitor_summary.json`, `exploratory_*.json`, and per-image public rows with messages stripped (`heldout_public_rows.json`).
- **Process records:** the pre-registration `study/PLAN.md` and the deviation log `study/DEVIATIONS.md`.
- **Withheld:** encoders, the reference decoder, messages, positive images and raw VLM answers on positives. Judges can still verify the hashes, the clean images, the detector code and all aggregates.

## Author Contributions

S.Y. conceived the study, made the design decisions, and is responsible for all claims.

## References

[1] N. Kezins, B. Chan, K. Reynoso, J. Chua. "How does Fable 5.1 hide messages in images?" LessWrong, 21 Oct 2026. https://www.lesswrong.com/posts/WHEQps5PK8LrrcTAb (authors as in the post's suggested citation; the byline reads Nikita Kezin, 13ryanC, hronir, James Chua).  
[2] S. Motwani et al. "Secret Collusion among AI Agents: Multi-Agent Deception via Steganography." arXiv:2402.07510.  
[3] R. Greenblatt et al. "AI Control: Improving Safety Despite Intentional Subversion." arXiv:2312.06942.  
[4] F. Roger, R. Greenblatt. "Preventing Language Models From Hiding Their Reasoning." arXiv:2310.18512.  
[5] A. Marafioti et al. "SmolVLM: Redefining small and efficient multimodal models." arXiv:2504.05299.  
[6] R. Smith. "An Overview of the Tesseract OCR Engine." ICDAR 2007.  
[7] E. B. Wilson. "Probable Inference, the Law of Succession, and Statistical Inference." JASA 22(158), 1927.

## Appendix A. Limitations and Dual-Use / Ethical Considerations

**Dual use.** Measuring hidden image channels helps defenders, but a detailed encoding recipe would help an attacker. We therefore publish only class-level descriptions, aggregate results and clean examples. Encoder parameters, reading orders, messages, positive images and the reference decoder are withheld. The scheme classes are already public at class level [1]. This work adds no new hiding capability beyond simple scripted encodings, and it gives defenders a falsifiable test harness.

**Misreading risk.** These results must not be read as evidence of real-world prevalence, of spontaneous collusion, or that jitter "solves" image steganography. Section 4.3 shows how a headline defense number can mislead. A detector that passes this benchmark is not a general steganalysis tool.

**Safety of the study itself.** All messages are benign words. No human subjects or personal data were involved. All models ran on the author's own machine and Azure VMs. No hosted model API saw any image.

**Limitations** are listed in Section 5.

## Appendix B. Deviations from the Pre-Registration

- **D1.** The original plan reused existing positives. No licensed positives were available, so we built our own encoders, with these guards: encoders frozen before detectors, a held-out variant, and private positives.
- **D2.** The sample size grew to 48 development and 96 held-out images.
- **D3.** The 2.2B receiver needed about 9 GB of fp32 weights, more than this 8 GB machine has, so we used the 500M model. This was decided before Azure access, and the primary was kept to respect the freeze.
- **D4.** We added the REF and R2 arms.
- **D5.** After F1, the LINE target line was redrawn on top of the series line, so the series no longer split its dashes. The change was re-frozen as F1b, before any detector code existed. REF fidelity after the fix was 959/960 on throwaway seeds and 24/24 on development.
- **D6 (timing).** The VLM arms ran on 9 Nov 2026, after the non-VLM held-out analysis, with frozen prompts and parser. A local run on Apple MPS was killed by memory pressure after 29 outputs. All 576 jobs were rerun on Azure CPU VMs, and the 29 local answers were identical to the Azure ones.
- **D7 (secondary receiver).** The Qwen2.5-VL-7B run was decided after the primary results were seen. It ran on Azure CPU because Modal GPUs required a payment method.
- **D8 (exploratory).** The GRID reader and the character-agreement scores (Section 4.3) were added after the results were seen.
- **D9 (replication).** A fresh 384-image split was made with the frozen generator, detectors and defenses, after all frozen results. Its environment parity check matched all 96 held-out results.
- **D10 (monitor stress tests).** Three monitor tests were added after all frozen results: a hinted monitor prompt, the Qwen2.5-VL-32B model, and an overt positive control.
- **D11 (threshold-free statistics).** Appendix C was added after all results. It uses only the frozen detector scores and grading keys.

## Appendix C. Threshold-Free Detector Analysis (exploratory)

Is a detector's miss caused by its frozen threshold or by its feature? AUROC answers this without any threshold. It is the chance that a random positive scores above a random clean image of the same carrier: 1.0 is perfect separation, and 0.5 is chance. Intervals are percentile bootstraps (5,000 resamples). Each carrier is scored by its own detector, with only that carrier's clean images as negatives.

**Table C1. Per-carrier detector AUROC (95% bootstrap CI), with the variant split.**

| Carrier (detector) | Held-out AUROC | Replication AUROC | Replication, variant A / B |
|---|---|---|---|
| LINE (dash anomaly) | 1.00 (1.00–1.00) | 1.00 (1.00–1.00) | 1.00 / 1.00 |
| RANK (first letter) | 0.99 (0.94–1.00) | 0.93 (0.87–0.97) | 1.00 / 0.86 |
| BAR (height lattice) | 0.63 (0.41–0.84) | 0.63 (0.51–0.74) | 1.00 / **0.25** |
| GRID (bit periodicity) | 0.54 (0.30–0.78) | 0.49 (0.37–0.61) | 0.45 / 0.52 |
| All, max of score/threshold | 0.85 (0.77–0.93) | 0.82 (0.78–0.87) | — |

Two failures are feature failures, not threshold failures. The GRID feature is at chance on both splits, so no threshold would catch GRID. On BAR, the feature separates variant A perfectly but scores every variant B chart exactly 0, the floor (6/6 held-out, 24/24 replication). That ties with half the clean charts and never exceeds any, giving AUROC 0.25. The feature does not respond to variant B at all, so recalibrating would not help; a defender needs a different feature.

**Exact tests (Fisher, two-sided; the last comparison is paired, so it is descriptive only).**

- Recall on variant A against variant B: 72/96 vs 39/96 on replication, p = 2.3×10⁻⁶. On the smaller held-out set it is 18/24 vs 11/24, p = 0.075.
- Detector false flags, held-out against replication: 1/48 vs 13/192, p = 0.31. The two estimates are consistent.
- The 500M monitor (V) recall against its false-flag rate: 30/48 vs 31/48, p = 1.0. It does not separate positives from clean images.
- False flags, detectors against the 500M monitor (V), on the same 48 clean images: 1/48 vs 31/48.

## LLM Usage Statement

AI coding assistants in Cursor, including Claude models, helped with planning, code, analysis scripts and drafting. The author made the design decisions, including building the encoders, choosing the guards and the freeze points. All numbers come from scripts in the repository, run on the author's machine and Azure VMs. The Fisher-test inputs in Appendix C are the reported counts. The author reviewed the claims and is responsible for them.
