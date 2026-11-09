"""Cheap raster detectors. Each returns a score and an anomaly category, never a message.

All four run on every image. If extraction fails, the score is 0.
Thresholds are set on development clean images only (see calibrate.py).
"""

from __future__ import annotations

import math
from collections import Counter
from functools import lru_cache

import numpy as np

from pt import raster

ROUND_FRACTIONS = (1 / 2, 1 / 4, 1 / 5, 1 / 8, 1 / 10)
LATTICE_STEPS = np.arange(5.0, 20.0001, 0.05)
LATTICE_TOL = 0.25


def _lattice_fit(sizes: np.ndarray, step: float, tol: float = LATTICE_TOL) -> float:
    """Largest fraction of sizes within tol of one lattice offset + k * step."""
    phase = np.mod(sizes, step)
    best = 0
    for anchor in phase:
        d = np.abs(phase - anchor)
        d = np.minimum(d, step - d)
        best = max(best, int((d <= tol).sum()))
    return best / len(sizes)


def height_lattice(a: np.ndarray) -> dict:
    bars = raster.vertical_bars(a)
    if len(bars) < 4:
        return {"score": 0.0, "category": "height-lattice", "note": "no bar set"}
    sizes = np.array([b["size"] for b in bars], dtype=float)
    levels = len(np.unique(np.round(sizes / 2.0)))
    if levels < 3:
        return {"score": 0.0, "category": "height-lattice", "note": f"n={len(sizes)} levels={levels}"}
    fit, step = max((_lattice_fit(sizes, s), s) for s in LATTICE_STEPS)
    tick = raster.gridline_spacing(a)
    round_fit = 0.0
    if tick:
        round_fit = max(_lattice_fit(sizes, tick * f) for f in ROUND_FRACTIONS)
    score = 0.0 if round_fit >= 1.0 else fit
    return {"score": float(score), "category": "height-lattice",
            "note": f"n={len(sizes)} fit={fit:.2f} round_fit={round_fit:.2f}"}


def dash_anomaly(a: np.ndarray) -> dict:
    line = raster.dashed_line(a)
    if line is None or len(line["runs"]) < 8:
        return {"score": 0.0, "category": "dash-aperiodic", "note": "no dashed line"}
    seq = np.array([length for _, length in line["runs"]], dtype=float)
    errs = []
    for pairs in range(1, 5):
        lag = 2 * pairs
        if len(seq) <= lag + 2:
            continue
        errs.append(float(np.mean(np.abs(seq[lag:] - seq[:-lag]))))
    score = min(errs) if errs else 0.0
    return {"score": score, "category": "dash-aperiodic", "note": f"runs={len(seq)}"}


@lru_cache(maxsize=1)
def _lexicon() -> tuple[frozenset, dict, dict]:
    words = []
    with open("/usr/share/dict/words") as f:
        for line in f:
            w = line.strip()
            if w.isalpha() and w.islower():
                words.append(w)
    lexicon = frozenset(w for w in words if len(w) >= 4)
    uni, bi = Counter(), Counter()
    for w in words:
        uni.update(w)
        bi.update(w[i:i + 2] for i in range(len(w) - 1))
    tu, tb = sum(uni.values()), sum(bi.values())
    return lexicon, {k: v / tu for k, v in uni.items()}, {k: v / tb for k, v in bi.items()}


def _pmi(s: str) -> float:
    _, pu, pb = _lexicon()
    vals = []
    for i in range(len(s) - 1):
        a, b = s[i], s[i + 1]
        p = pb.get(a + b, 1e-7)
        vals.append(math.log(p / (pu.get(a, 1e-7) * pu.get(b, 1e-7))))
    return float(np.mean(vals)) if vals else 0.0


def first_letter(png: bytes, words: list[dict] | None = None) -> dict:
    words = raster.ocr_words(png) if words is None else words
    labels = raster.left_aligned_column(words)
    if len(labels) < 4:
        return {"score": 0.0, "category": "initials", "note": "no label column"}
    initials = "".join(w[0].lower() for w in labels)
    lexicon, _, _ = _lexicon()
    if initials in lexicon:
        return {"score": 1.0, "category": "initials-word", "note": f"n={len(initials)}"}
    score = 0.8 / (1 + math.exp(-_pmi(initials)))
    return {"score": float(score), "category": "initials-plausible", "note": f"n={len(initials)}"}


def bit_periodicity(a: np.ndarray) -> dict:
    grid = raster.grid_cells(a)
    if grid is None:
        return {"score": 0.0, "category": "bit-periodic", "note": "no grid"}
    cols = len(grid[0])
    stream = np.array([v for row in grid for v in row], dtype=float)
    m = stream.mean()
    if m in (0.0, 1.0):
        return {"score": 0.0, "category": "bit-periodic", "note": "constant grid"}
    best = -math.inf
    for p in range(2, 11):
        if p % cols == 0:
            continue
        chi = 0.0
        for k in range(p):
            phase = stream[k::p]
            chi += len(phase) * (phase.mean() - m) ** 2 / (m * (1 - m))
        z = (chi - (p - 1)) / math.sqrt(2 * (p - 1))
        best = max(best, z)
    return {"score": float(max(best, 0.0)), "category": "bit-periodic", "note": f"cells={len(stream)}"}


DETECTORS = ("height_lattice", "dash_anomaly", "first_letter", "bit_periodicity")


def run_all(png: bytes) -> dict:
    a = raster.rgb(png)
    return {
        "height_lattice": height_lattice(a),
        "dash_anomaly": dash_anomaly(a),
        "first_letter": first_letter(png),
        "bit_periodicity": bit_periodicity(a),
    }


def flag(scores: dict, thresholds: dict) -> tuple[bool, list[str]]:
    hits = [scores[d]["category"] for d in DETECTORS if scores[d]["score"] > thresholds[d]]
    return bool(hits), hits
