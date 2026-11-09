"""Build report-ready public tables from held-out aggregate results.

This script reads only `runs/heldout_summary.json`, which contains aggregate
counts and no messages or encoder details.
"""

from __future__ import annotations

import json
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
SUMMARY_PATH = STUDY / "runs" / "heldout_summary.json"
OUT_PATH = STUDY / "runs" / "report_tables.md"


def pct(x: float | None) -> str:
    if x is None:
        return "n/a"
    return f"{100 * x:.1f}%"


def count_rate(metric: dict) -> str:
    return f"{metric['numerator']}/{metric['denominator']} ({pct(metric['rate'])})"


def ci(metric: dict) -> str:
    low, high = metric["wilson95"]
    if low is None or high is None:
        return "n/a"
    return f"{pct(low)}-{pct(high)}"


def table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    out.extend("| " + " | ".join(row) + " |" for row in rows)
    return out


def detection_rows(summary: dict) -> list[list[str]]:
    rows = []
    for carrier in sorted(summary["by_carrier"]):
        det = summary["by_carrier"][carrier]["detection"]
        rows.append([
            carrier,
            str(det["tp"]),
            str(det["fn"]),
            str(det["fp"]),
            str(det["tn"]),
            count_rate(det["recall"]),
            ci(det["recall"]),
            count_rate(det["false_flag_rate"]),
            ci(det["false_flag_rate"]),
        ])
    det = summary["detection"]
    rows.append([
        "Overall",
        str(det["tp"]),
        str(det["fn"]),
        str(det["fp"]),
        str(det["tn"]),
        count_rate(det["recall"]),
        ci(det["recall"]),
        count_rate(det["false_flag_rate"]),
        ci(det["false_flag_rate"]),
    ])
    return rows


def recovery_rows(summary: dict) -> list[list[str]]:
    rows = []
    for carrier in sorted(summary["by_carrier"]):
        rec = summary["by_carrier"][carrier]["reference_recovery"]
        rows.append([
            carrier,
            count_rate(rec["original_v"]),
            count_rate(rec["jitter_r"]),
            count_rate(rec["canonical_r2"]),
        ])
    rec = summary["reference_recovery"]
    rows.append([
        "Overall",
        count_rate(rec["original_v"]),
        count_rate(rec["jitter_r"]),
        count_rate(rec["canonical_r2"]),
    ])
    return rows


def utility_rows(summary: dict) -> list[list[str]]:
    rows = []
    for carrier in sorted(summary["by_carrier"]):
        util = summary["by_carrier"][carrier]["objective_utility"]
        rows.append([
            carrier,
            count_rate(util["jitter_r"]),
            count_rate(util["canonical_r2"]),
        ])
    util = summary["objective_utility"]
    rows.append([
        "Overall",
        count_rate(util["jitter_r"]),
        count_rate(util["canonical_r2"]),
    ])
    return rows


def variant_rows(summary: dict) -> list[list[str]]:
    rows = []
    for variant in sorted(summary["by_variant"]):
        rec = summary["by_variant"][variant]["reference_recovery"]
        rows.append([
            variant,
            str(summary["by_variant"][variant]["n_positive"]),
            count_rate(rec["original_v"]),
            count_rate(rec["jitter_r"]),
            count_rate(rec["canonical_r2"]),
        ])
    return rows


def build(summary: dict) -> str:
    det = summary["detection"]
    rec = summary["reference_recovery"]
    util = summary["objective_utility"]
    lines = [
        "# Pixel Tripwire Report Tables",
        "",
        "Generated from `study/runs/heldout_summary.json`. Counts are held-out only.",
        "Wilson intervals are 95%. No private messages, encoder details, or decoded strings are included.",
        "",
        "## Headline Counts",
        "",
        *table(
            ["Metric", "Count", "Rate", "Wilson 95% CI"],
            [
                ["Detector recall", f"{det['recall']['numerator']}/{det['recall']['denominator']}", pct(det["recall"]["rate"]), ci(det["recall"])],
                ["Detector false-flag rate", f"{det['false_flag_rate']['numerator']}/{det['false_flag_rate']['denominator']}", pct(det["false_flag_rate"]["rate"]), ci(det["false_flag_rate"])],
                ["REF original recovery", f"{rec['original_v']['numerator']}/{rec['original_v']['denominator']}", pct(rec["original_v"]["rate"]), ci(rec["original_v"])],
                ["REF jitter recovery", f"{rec['jitter_r']['numerator']}/{rec['jitter_r']['denominator']}", pct(rec["jitter_r"]["rate"]), ci(rec["jitter_r"])],
                ["REF canonical recovery", f"{rec['canonical_r2']['numerator']}/{rec['canonical_r2']['denominator']}", pct(rec["canonical_r2"]["rate"]), ci(rec["canonical_r2"])],
                ["Jitter utility preserved", f"{util['jitter_r']['numerator']}/{util['jitter_r']['denominator']}", pct(util["jitter_r"]["rate"]), ci(util["jitter_r"])],
                ["Canonical utility preserved", f"{util['canonical_r2']['numerator']}/{util['canonical_r2']['denominator']}", pct(util["canonical_r2"]["rate"]), ci(util["canonical_r2"])],
            ],
        ),
        "",
        "## Detector Results By Carrier",
        "",
        *table(
            ["Carrier", "TP", "FN", "FP", "TN", "Recall", "Recall CI", "False flags", "False-flag CI"],
            detection_rows(summary),
        ),
        "",
        "## Reference Recovery By Carrier",
        "",
        *table(
            ["Carrier", "Original V", "Jitter R", "Canonical R2"],
            recovery_rows(summary),
        ),
        "",
        "## Objective Utility By Carrier",
        "",
        *table(
            ["Carrier", "Jitter R", "Canonical R2"],
            utility_rows(summary),
        ),
        "",
        "## Reference Recovery By Held-Out Variant",
        "",
        *table(
            ["Variant", "N positives", "Original V", "Jitter R", "Canonical R2"],
            variant_rows(summary),
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    summary = json.loads(SUMMARY_PATH.read_text())
    OUT_PATH.write_text(build(summary), encoding="utf-8")
    print(f"wrote {OUT_PATH.relative_to(STUDY)}")


if __name__ == "__main__":
    main()
