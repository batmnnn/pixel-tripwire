"""Render report.md to report.html and report.pdf with headless Chrome."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: A4; margin: 15mm 16mm 15mm 16mm; }
body { font-family: "Times New Roman", Times, serif; font-size: 10.5pt; line-height: 1.27; color: #111; }
h1 { font-size: 16pt; text-align: center; margin: 0 0 6pt; line-height: 1.2; }
h1 + p { text-align: center; margin-top: 0; }
h2 { font-size: 12pt; margin: 12pt 0 4pt; }
h3 { font-size: 10.5pt; margin: 9pt 0 3pt; }
p { margin: 0 0 5pt; text-align: justify; }
ul, ol { margin: 0 0 5pt; padding-left: 18pt; }
li { margin-bottom: 2pt; }
table { border-collapse: collapse; margin: 4pt auto 6pt; font-size: 9pt; page-break-inside: avoid; }
th, td { border-top: 1px solid #999; border-bottom: 1px solid #999; padding: 2pt 5pt; }
th { background: #f0f0f0; }
img { display: block; margin: 4pt auto 2pt; max-width: 92%; }
img[alt="Figure 1"] { max-width: 62%; }
img[alt="Figure 3"] { max-width: 78%; }
img[alt="Figure 2"] { max-width: 68%; }
em { font-style: italic; }
code { font-size: 9pt; }
h2#appendix-a-limitations-and-dual-use-ethical-considerations { margin-top: 18pt; }
h2[id^="appendix-c"] { page-break-before: always; }
"""


def main() -> None:
    text = (HERE / "report.md").read_text()
    left = re.findall(r"\{\{[A-Z_]+\}\}", text)
    if left:
        raise SystemExit(f"unfilled placeholders: {left}")
    body = markdown.markdown(text, extensions=["tables", "toc"])
    html = f"<!doctype html><html><head><meta charset='utf-8'><title>Pixel Tripwire</title><style>{CSS}</style></head><body>{body}</body></html>"
    (HERE / "report.html").write_text(html)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={HERE / 'report.pdf'}", (HERE / "report.html").as_uri()],
                   check=True, capture_output=True, timeout=120)
    print(HERE / "report.pdf")


if __name__ == "__main__":
    main()
