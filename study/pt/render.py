"""Safe SVG -> PNG rendering with CairoSVG in its default safe mode."""

from __future__ import annotations

import hashlib
import io

import cairosvg
from PIL import Image

MAX_SVG_BYTES = 200_000
REFUSED = (b"<script", b"<!entity", b"<!doctype", b"xlink:href", b"url(", b"javascript:", b"<image", b"<foreignobject")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_svg(svg: bytes) -> None:
    if len(svg) > MAX_SVG_BYTES:
        raise ValueError("svg too large")
    lowered = svg.lower()
    for token in REFUSED:
        if token in lowered:
            raise ValueError(f"refused svg content: {token.decode()}")


def svg_to_png(svg: str | bytes, width: int = 640, height: int = 420) -> bytes:
    data = svg.encode() if isinstance(svg, str) else svg
    check_svg(data)
    png = cairosvg.svg2png(
        bytestring=data,
        output_width=width,
        output_height=height,
        background_color="white",
        unsafe=False,
    )
    image = Image.open(io.BytesIO(png)).convert("RGB")
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def load_rgb(png: bytes) -> Image.Image:
    return Image.open(io.BytesIO(png)).convert("RGB")
