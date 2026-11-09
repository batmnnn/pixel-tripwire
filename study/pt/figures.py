"""PUBLIC. Report figures from clean images and aggregate results only."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

STUDY = Path(__file__).resolve().parents[1]
OUT = STUDY / "report" / "figures"
CARRIERS = ["BAR", "LINE", "RANK", "GRID"]


def clean_examples() -> None:
    rows = json.loads((STUDY / "runs" / "heldout_public_rows.json").read_text())
    picks = {}
    for r in rows:
        if r["label"] == "clean" and r["carrier"] not in picks:
            picks[r["carrier"]] = r["image_id"]
    fig, axes = plt.subplots(2, 2, figsize=(8, 5.4))
    for ax, carrier in zip(axes.flat, CARRIERS):
        ax.imshow(Image.open(STUDY / "data" / "heldout" / f"{picks[carrier]}.png"))
        ax.set_title(f"{carrier} (clean)", fontsize=10)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "fig1_clean_examples.png", dpi=200)
    plt.close(fig)


def recovery_by_carrier() -> None:
    s = json.loads((STUDY / "runs" / "heldout_summary.json").read_text())
    by = s["by_carrier"]
    arms = [("original_v", "Original"), ("jitter_r", "Jitter (R, J=6)"), ("canonical_r2", "Canonicalize (R2)")]
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    width = 0.26
    for i, (key, name) in enumerate(arms):
        vals = [by[c]["reference_recovery"][key]["numerator"] for c in CARRIERS]
        bars = ax.bar([x + (i - 1) * width for x in range(4)], vals, width, label=name)
        ax.bar_label(bars, fontsize=7)
    grid = json.loads((STUDY / "runs" / "exploratory_grid_jitter.json").read_text())
    ax.scatter([3 - width, 3], [grid["label_anchored_original"], grid["label_anchored_jitter"]],
               marker="D", color="black", zorder=3, s=22, label="GRID exploratory reader (post-freeze)")
    ax.set_xticks(range(4), CARRIERS)
    ax.set_ylabel("Exact recoveries (of 12)")
    ax.set_ylim(0, 13.5)
    ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=4, frameon=False)
    ax.set_title("Scripted reference decoder recovery on held-out positives", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig2_recovery.png", dpi=200)
    plt.close(fig)


def monitors() -> None:
    small = json.loads((STUDY / "runs" / "heldout_vlm_summary.json").read_text())["detection"]
    big = json.loads((STUDY / "runs" / "heldout_qwen7b_summary.json").read_text())["detection"]
    points = [
        ("Text-only (both models)", small["T"], "s", "gray"),
        ("SmolVLM2-500M, original", small["V"], "o", "tab:orange"),
        ("SmolVLM2-500M, jittered", small["R"], "o", "tab:red"),
        ("Qwen2.5-VL-7B, original/jittered", big["V"], "^", "tab:purple"),
        ("Raster detectors (C)", small["C"], "D", "tab:blue"),
        ("C or 500M-R (CMB)", small["CMB"], "P", "tab:green"),
    ]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot([0, 1], [0, 1], ls=":", color="gray", lw=1)
    for name, d, marker, color in points:
        x, y = d["false_flag"]["rate"], d["recall"]["rate"]
        xl, xh = d["false_flag"]["ci95"]
        yl, yh = d["recall"]["ci95"]
        ax.errorbar(x, y, xerr=[[x - xl], [xh - x]], yerr=[[y - yl], [yh - y]], fmt=marker, color=color,
                    ms=7, capsize=2, lw=0.8, label=name)
    ax.set_xlim(-0.03, 1)
    ax.set_ylim(-0.03, 1)
    ax.set_xlabel("False-flag rate on 48 clean images")
    ax.set_ylabel("Recall on 48 positives")
    ax.legend(fontsize=7, loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False)
    ax.set_title("Held-out monitors (95% Wilson intervals); dotted line = chance", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_monitors.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    clean_examples()
    recovery_by_carrier()
    monitors()
    print(sorted(p.name for p in OUT.iterdir()))
