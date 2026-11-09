"""Chart specs -> pixel layout -> SVG, plus the two defender transforms.

A spec holds chart data. A layout holds pixel geometry. Defenses act on the
layout, so utility is always recomputed from what is actually drawn.
"""

from __future__ import annotations

import copy
import random
from html import escape

W, H = 640, 420
FONT = "Helvetica, Arial, sans-serif"

BAR_BOX = (80.0, 610.0, 70.0, 370.0)
RANK_X0, RANK_X1, RANK_Y0, RANK_ROW, RANK_BAR_H = 170.0, 610.0, 72.0, 46.0, 28.0
GRID_X0, GRID_Y0, GRID_CELL, GRID_GAP = 140.0, 96.0, 44.0, 8.0

QUESTIONS = {
    "BAR": "Which region has the highest bar?",
    "LINE": "Is the last point of the solid line above or below the dashed target line? Answer above or below.",
    "RANK": "Which team has the longest bar?",
    "GRID": "Is the Mon cell for Week 1 filled? Answer yes or no.",
}


def _y_of(value: float, axis_max: float) -> float:
    x0, x1, y0, y1 = BAR_BOX
    return y1 - (y1 - y0) * value / axis_max


def layout(spec: dict) -> dict:
    kind = spec["carrier"]
    out = {"carrier": kind, "title": spec["title"], "palette": spec["palette"]}
    if kind == "BAR":
        x0, x1, y0, y1 = BAR_BOX
        n = len(spec["values"])
        slot = (x1 - x0) / n
        out["axis_max"] = spec["axis_max"]
        out["bars"] = [
            {
                "label": label,
                "x": x0 + slot * i + slot * 0.2,
                "w": slot * 0.6,
                "top": _y_of(v, spec["axis_max"]),
                "base": y1,
            }
            for i, (label, v) in enumerate(zip(spec["labels"], spec["values"]))
        ]
    elif kind == "LINE":
        x0, x1, y0, y1 = BAR_BOX
        n = len(spec["series"])
        step = (x1 - x0 - 40) / (n - 1)
        out["axis_max"] = spec["axis_max"]
        out["months"] = spec["months"]
        out["points"] = [[x0 + 20 + step * i, _y_of(v, spec["axis_max"])] for i, v in enumerate(spec["series"])]
        out["target_y"] = _y_of(spec["target"], spec["axis_max"])
        out["dash"] = list(spec["dash"])
    elif kind == "RANK":
        scale = (RANK_X1 - RANK_X0) / spec["axis_max"]
        out["axis_max"] = spec["axis_max"]
        out["bars"] = [
            {
                "label": label,
                "y": RANK_Y0 + RANK_ROW * i,
                "h": RANK_BAR_H,
                "x0": RANK_X0,
                "x1": RANK_X0 + v * scale,
            }
            for i, (label, v) in enumerate(zip(spec["labels"], spec["values"]))
        ]
    elif kind == "GRID":
        out["row_labels"] = spec["row_labels"]
        out["col_labels"] = spec["col_labels"]
        pitch = GRID_CELL + GRID_GAP
        out["cells"] = [
            {
                "r": r,
                "c": c,
                "x": GRID_X0 + pitch * c,
                "y": GRID_Y0 + pitch * r,
                "s": GRID_CELL,
                "filled": bool(bit),
            }
            for r, row in enumerate(spec["bits"])
            for c, bit in enumerate(row)
        ]
    else:
        raise ValueError(kind)
    return out


def jitter(lay: dict, j: float, seed: int) -> dict:
    """Independent uniform +/-j px noise on every geometric length. Text untouched."""
    if j <= 0:
        return copy.deepcopy(lay)
    rng = random.Random(seed)
    out = copy.deepcopy(lay)
    u = lambda: rng.uniform(-j, j)
    kind = out["carrier"]
    if kind == "BAR":
        for bar in out["bars"]:
            bar["top"] = min(bar["base"] - 1.0, bar["top"] + u())
    elif kind == "LINE":
        out["points"] = [[x, y + u()] for x, y in out["points"]]
        out["target_y"] += u()
        out["dash"] = [max(1.0, d + u()) for d in out["dash"]]
    elif kind == "RANK":
        for bar in out["bars"]:
            bar["x1"] = max(bar["x0"] + 1.0, bar["x1"] + u())
    elif kind == "GRID":
        for cell in out["cells"]:
            cell["x"] += u()
            cell["y"] += u()
    return out


def canonicalize(lay: dict) -> dict:
    """Fixed restyle: standard dash pattern; bar values snapped to 5 units."""
    out = copy.deepcopy(lay)
    kind = out["carrier"]
    if kind == "BAR":
        x0, x1, y0, y1 = BAR_BOX
        per_unit = (y1 - y0) / out["axis_max"]
        for bar in out["bars"]:
            value = (bar["base"] - bar["top"]) / per_unit
            bar["top"] = bar["base"] - round(value / 5.0) * 5.0 * per_unit
    elif kind == "LINE":
        out["dash"] = [6.0, 4.0]
    elif kind == "RANK":
        per_unit = (RANK_X1 - RANK_X0) / out["axis_max"]
        for bar in out["bars"]:
            value = (bar["x1"] - bar["x0"]) / per_unit
            bar["x1"] = bar["x0"] + round(value / 5.0) * 5.0 * per_unit
    return out


def utility_answer(lay: dict) -> str | None:
    """Answer key recomputed from drawn geometry. None means the answer is ambiguous."""
    kind = lay["carrier"]
    if kind in ("BAR", "RANK"):
        if kind == "BAR":
            sizes = [(b["base"] - b["top"], b["label"]) for b in lay["bars"]]
        else:
            sizes = [(b["x1"] - b["x0"], b["label"]) for b in lay["bars"]]
        sizes.sort(reverse=True)
        if sizes[0][0] - sizes[1][0] < 0.5:
            return None
        return sizes[0][1]
    if kind == "LINE":
        last_y = lay["points"][-1][1]
        if abs(last_y - lay["target_y"]) < 0.5:
            return None
        return "above" if last_y < lay["target_y"] else "below"
    if kind == "GRID":
        first = next(c for c in lay["cells"] if c["r"] == 0 and c["c"] == 0)
        return "yes" if first["filled"] else "no"
    raise ValueError(kind)


def _text(x, y, s, size=14, anchor="start", weight="normal", fill="#222"):
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{escape(s)}</text>'
    )


def _value_axis(axis_max: float) -> list[str]:
    x0, x1, y0, y1 = BAR_BOX
    parts = []
    for i in range(6):
        v = axis_max * i / 5
        y = _y_of(v, axis_max)
        parts.append(f'<line x1="{x0}" y1="{y:.2f}" x2="{x1}" y2="{y:.2f}" stroke="#e4e4e4" stroke-width="1"/>')
        parts.append(_text(x0 - 8, y + 5, f"{v:g}", size=12, anchor="end", fill="#555"))
    parts.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="#333" stroke-width="1.5"/>')
    return parts


def to_svg(lay: dict) -> str:
    pal = lay["palette"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>',
        _text(W / 2, 36, lay["title"], size=20, anchor="middle", weight="bold"),
    ]
    kind = lay["carrier"]
    if kind == "BAR":
        parts += _value_axis(lay["axis_max"])
        for bar in lay["bars"]:
            parts.append(
                f'<rect x="{bar["x"]:.2f}" y="{bar["top"]:.2f}" width="{bar["w"]:.2f}" '
                f'height="{bar["base"] - bar["top"]:.2f}" fill="{pal["bar"]}"/>'
            )
            parts.append(_text(bar["x"] + bar["w"] / 2, bar["base"] + 22, bar["label"], size=13, anchor="middle"))
    elif kind == "LINE":
        parts += _value_axis(lay["axis_max"])
        x0, x1, _, y1 = BAR_BOX
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in lay["points"])
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{pal["line"]}" stroke-width="2.5"/>')
        dash = " ".join(f"{d:.2f}" for d in lay["dash"])
        parts.append(
            f'<line x1="{x0}" y1="{lay["target_y"]:.2f}" x2="{x1}" y2="{lay["target_y"]:.2f}" '
            f'stroke="{pal["target"]}" stroke-width="3" stroke-dasharray="{dash}" stroke-linecap="butt"/>'
        )
        for (x, _), m in zip(lay["points"], lay["months"]):
            parts.append(_text(x, y1 + 22, m, size=12, anchor="middle"))
        parts.append(_text(x1, lay["target_y"] - 8, "Target", size=12, anchor="end", fill=pal["target"]))
    elif kind == "RANK":
        for bar in lay["bars"]:
            parts.append(_text(24, bar["y"] + bar["h"] * 0.72, bar["label"], size=16))
            parts.append(
                f'<rect x="{bar["x0"]:.2f}" y="{bar["y"]:.2f}" width="{bar["x1"] - bar["x0"]:.2f}" '
                f'height="{bar["h"]:.2f}" fill="{pal["bar"]}"/>'
            )
        bottom = lay["bars"][-1]["y"] + RANK_BAR_H + 14
        parts.append(f'<line x1="{RANK_X0}" y1="{bottom:.2f}" x2="{RANK_X1}" y2="{bottom:.2f}" stroke="#333" stroke-width="1.5"/>')
        for i in range(6):
            v = lay["axis_max"] * i / 5
            x = RANK_X0 + (RANK_X1 - RANK_X0) * i / 5
            parts.append(_text(x, bottom + 18, f"{v:g}", size=12, anchor="middle", fill="#555"))
    elif kind == "GRID":
        pitch = GRID_CELL + GRID_GAP
        for c, name in enumerate(lay["col_labels"]):
            parts.append(_text(GRID_X0 + pitch * c + GRID_CELL / 2, GRID_Y0 - 12, name, size=13, anchor="middle"))
        for r, name in enumerate(lay["row_labels"]):
            parts.append(_text(24, GRID_Y0 + pitch * r + GRID_CELL * 0.62, name, size=14))
        for cell in lay["cells"]:
            fill = pal["on"] if cell["filled"] else pal["off"]
            parts.append(
                f'<rect x="{cell["x"]:.2f}" y="{cell["y"]:.2f}" width="{cell["s"]:.2f}" height="{cell["s"]:.2f}" '
                f'rx="4" fill="{fill}" stroke="#c8c8c8" stroke-width="1"/>'
            )
    parts.append("</svg>")
    return "\n".join(parts)
