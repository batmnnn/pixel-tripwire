"""Raster-only extraction: bars, dashed lines, OCR text columns, and grid cells.

Nothing here reads SVG, labels, or specs. Every function works on a PNG.
"""

from __future__ import annotations

import csv
import io
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def rgb(png: bytes) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(np.int16)


def saturation(a: np.ndarray) -> np.ndarray:
    return a.max(axis=2) - a.min(axis=2)


def rectangles(a: np.ndarray, min_area: int = 120) -> list[dict]:
    """Solid saturated rectangles (bars or filled cells)."""
    mask = saturation(a) > 40
    lab, n = ndimage.label(mask)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        if sl is None:
            continue
        ys, xs = sl
        h, w = ys.stop - ys.start, xs.stop - xs.start
        area = int((lab[sl] == i).sum())
        if area < min_area or area < 0.85 * h * w:
            continue
        sub = (lab[sl] == i).astype(float)
        cols = sub.mean(axis=0)
        rows = sub.mean(axis=1)
        out.append({
            "x0": xs.start + (1 - cols[0]), "x1": xs.stop - (1 - cols[-1]),
            "y0": ys.start + (1 - rows[0]), "y1": ys.stop - (1 - rows[-1]),
            "w": w, "h": h,
        })
    return out


def vertical_bars(a: np.ndarray) -> list[dict]:
    """Bars sharing a common baseline, left to right, with sub-pixel heights."""
    rects = [r for r in rectangles(a) if r["h"] > 2 and r["w"] >= 20]
    if len(rects) < 3:
        return []
    bottoms = np.array([r["y1"] for r in rects])
    base = np.median(bottoms)
    rects = [r for r in rects if abs(r["y1"] - base) <= 2.0]
    rects.sort(key=lambda r: r["x0"])
    sat = saturation(a).astype(float)
    for r in rects:
        r["size"] = _subpixel_height(sat, r)
    return rects


def _subpixel_height(sat: np.ndarray, r: dict) -> float:
    """Sum of fractional coverage down the bar's center column, from anti-aliasing."""
    x = int((r["x0"] + r["x1"]) / 2)
    top, bottom = int(r["y0"]), int(np.ceil(r["y1"]))
    col = sat[max(top - 2, 0):bottom + 2, x]
    interior = np.median(sat[top + 2:bottom - 2, x]) if bottom - top > 6 else col.max()
    return float(np.clip(col / max(interior, 1.0), 0, 1).sum())


def horizontal_bars(a: np.ndarray) -> list[dict]:
    rects = [r for r in rectangles(a) if r["h"] >= 18 and r["h"] <= 40 and r["w"] > 2]
    if len(rects) < 3:
        return []
    left = np.median([r["x0"] for r in rects])
    rects = [r for r in rects if abs(r["x0"] - left) <= 2.0]
    rects.sort(key=lambda r: r["y0"])
    for r in rects:
        r["size"] = r["x1"] - r["x0"]
    return rects


def gridline_spacing(a: np.ndarray) -> float | None:
    """Spacing of light horizontal gridlines, if any."""
    light = (a.min(axis=2) > 200) & (a.max(axis=2) < 250) & (saturation(a) < 8)
    frac = light[:, 80:610].mean(axis=1)
    rows = np.where(frac > 0.25)[0]
    if len(rows) < 3:
        return None
    groups = np.split(rows, np.where(np.diff(rows) > 1)[0] + 1)
    centers = np.array([g.mean() for g in groups])
    if len(centers) < 3:
        return None
    return float(np.median(np.diff(centers)))


def dashed_line(a: np.ndarray, x0: int = 80, x1: int = 610, y_min: int = 60, y_max: int = 375) -> dict | None:
    """Find the plot-area row with the most on/off transitions and measure its runs.

    The title band and axis labels sit outside [y_min, y_max] and are excluded.
    """
    region = a[:, x0:x1]
    ink = region.min(axis=2) < 200
    transitions = np.abs(np.diff(ink.astype(np.int8), axis=1)).sum(axis=1)
    transitions[:y_min] = 0
    transitions[y_max:] = 0
    y = int(np.argmax(transitions))
    if transitions[y] < 10:
        return None
    def mode_color(yy: int) -> np.ndarray | None:
        px = region[yy][ink[yy]]
        if len(px) < 40:
            return None
        values, counts = np.unique(px, axis=0, return_counts=True)
        return values[int(np.argmax(counts))].astype(float) if counts.max() >= 40 else None

    seed_color = mode_color(y)
    if seed_color is None:
        return None
    # Edge rows of an anti-aliased line are blends of the line color with white,
    # so the true color lies on the white -> seed_color ray, farther from white.
    axis = 255 - seed_color
    color, best_t = seed_color, 1.0
    for yy in range(max(0, y - 3), min(a.shape[0], y + 4)):
        c = mode_color(yy)
        if c is None:
            continue
        t = float(np.dot(255 - c, axis) / max(np.dot(axis, axis), 1.0))
        if np.abs((255 - c) - t * axis).max() <= 12 and t > best_t:
            color, best_t = c, t

    ref = max(float(np.abs(255 - color).max()), 1.0)

    def row_coverage(yy: int) -> np.ndarray:
        """1 at the line color, 0 at white. Other colors score low on their worst channel."""
        dist = np.abs(region[yy] - color).max(axis=1)
        return np.clip(1 - dist / ref, 0, 1)

    band = [yy for yy in range(max(0, y - 3), min(a.shape[0], y + 4)) if transitions[yy] >= 0.6 * transitions[y]]
    def sharpness(yy: int) -> float:
        cov = row_coverage(yy)
        on_cov = cov[cov > 0.5]
        return float(on_cov.mean()) if len(on_cov) else 0.0

    yc = max(band, key=sharpness)
    coverage = row_coverage(yc)
    on = coverage > 0.72
    runs = []
    start, state = 0, bool(on[0])
    for i in range(1, len(on) + 1):
        if i == len(on) or bool(on[i]) != state:
            if state:
                length = float(coverage[max(start - 1, 0):min(i + 1, len(on))].sum())
            else:
                length = float((1 - coverage[start:i]).sum())
            runs.append((state, length, start, i))
            if i < len(on):
                start, state = i, bool(on[i])
    while runs and not runs[0][0]:
        runs.pop(0)
    if runs:
        runs.pop()
    return {"y": yc, "runs": [(s, l) for s, l, _, _ in runs]}


def ocr_words(png: bytes, scale: int = 3) -> list[dict]:
    """Tesseract word boxes in original pixel coordinates."""
    img = Image.open(io.BytesIO(png)).convert("L")
    img = img.resize((img.width * scale, img.height * scale), Image.LANCZOS)
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "in.png"
        img.save(path)
        res = subprocess.run(
            ["tesseract", str(path), "stdout", "--psm", "11", "tsv"],
            capture_output=True, text=True, timeout=60,
        )
    words = []
    for row in csv.DictReader(io.StringIO(res.stdout), delimiter="\t", quoting=csv.QUOTE_NONE):
        text = (row.get("text") or "").strip()
        try:
            conf = float(row.get("conf", -1))
        except ValueError:
            continue
        if not text or conf < 30:
            continue
        words.append({
            "text": text, "conf": conf,
            "x": int(row["left"]) / scale, "y": int(row["top"]) / scale,
            "w": int(row["width"]) / scale, "h": int(row["height"]) / scale,
        })
    return words


def left_aligned_column(words: list[dict], tol: float = 6.0, min_items: int = 4) -> list[str]:
    """Longest set of alphabetic words sharing a left edge, top to bottom."""
    alpha = [w for w in words if w["text"].isalpha() and len(w["text"]) >= 2]
    best: list[dict] = []
    for anchor in alpha:
        group = [w for w in alpha if abs(w["x"] - anchor["x"]) <= tol]
        if len(group) > len(best):
            best = group
    if len(best) < min_items:
        return []
    best.sort(key=lambda w: w["y"])
    return [_title_case_fix(w["text"]) for w in best]


def _title_case_fix(text: str) -> str:
    """Tesseract reads a capital I in Helvetica as l at the start of a capitalized label."""
    if len(text) >= 2 and text[0] == "l" and text[1].islower():
        return "I" + text[1:]
    return text


def grid_cells(a: np.ndarray) -> list[list[int]] | None:
    """Square cells with a border; filled if saturated. Rows and columns by clustering centers."""
    not_white = a.min(axis=2) < 248
    lab, n = ndimage.label(not_white)
    cells = []
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        if sl is None:
            continue
        ys, xs = sl
        h, w = ys.stop - ys.start, xs.stop - xs.start
        if not (36 <= h <= 52 and 36 <= w <= 52 and abs(h - w) <= 4):
            continue
        inner = a[ys.start + 6: ys.stop - 6, xs.start + 6: xs.stop - 6]
        filled = float(saturation(inner).mean()) > 40
        cells.append(((ys.start + ys.stop) / 2, (xs.start + xs.stop) / 2, int(filled)))
    if len(cells) < 14:
        return None

    def cluster(values: list[float]) -> list[float]:
        values = sorted(values)
        groups = [[values[0]]]
        for v in values[1:]:
            if v - groups[-1][-1] > 20:
                groups.append([v])
            else:
                groups[-1].append(v)
        return [float(np.mean(g)) for g in groups]

    row_c = cluster([c[0] for c in cells])
    col_c = cluster([c[1] for c in cells])
    grid = [[-1] * len(col_c) for _ in row_c]
    for cy, cx, f in cells:
        r = int(np.argmin([abs(cy - v) for v in row_c]))
        c = int(np.argmin([abs(cx - v) for v in col_c]))
        grid[r][c] = f
    if any(v < 0 for row in grid for v in row):
        return None
    return grid
