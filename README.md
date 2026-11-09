# Pixel Tripwire

A frozen, pre-registered synthetic benchmark for hidden content in agent-to-agent chart images.
It was built for the Apart Research Swarm Alignment Hackathon 2026, Track 4.

**Report:** [`study/report/report.pdf`](study/report/report.pdf). The source is `report.md`, built with `build.py`.

## Layout

| Path | Contents |
|---|---|
| `study/pt/` | Public code: chart generator, renderer, raster tools, the four structural detectors, VLM prompts and parser, figures |
| `study/freeze/` | Freezes F1, F1b and F2, with SHA-256 hashes of the code, inputs and parser, recorded before the held-out data existed |
| `study/runs/` | Aggregate results: held-out, replication and monitor stress tests, plus the exploratory analyses (labeled as such) |
| `study/data/heldout_clean/` | The 48 clean held-out images |
| `study/data/manifest_heldout.csv` | All 96 held-out image IDs, task briefs and image SHA-256 hashes. Labels are sealed. |
| `study/PLAN.md` | Pre-registration |
| `study/DEVIATIONS.md` | Every deviation from it (D1–D11) |

## Verify the freeze hashes

```bash
cd study && python3 -c "
import json, hashlib
for f in ['F1b', 'F2']:
    for p, h in json.load(open(f'freeze/{f}.json'))['sha256'].items():
        try:
            ok = hashlib.sha256(open(p, 'rb').read()).hexdigest() == h
            print(f, p, 'OK' if ok else 'MISMATCH')
        except FileNotFoundError:
            print(f, p, 'withheld')
"
```

Entries under `private/` hash files that are withheld. F1's `pt/charts.py` hash predates the recorded F1b fix (deviation D5).

## Withheld (dual use)

These are withheld:
- encoders
- the reference decoder
- messages
- positive images
- raw VLM answers on positives

All code was written during the sprint, 7–9 Nov 2026.
