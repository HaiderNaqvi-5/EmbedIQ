"""Extract a compact, chromatic brand palette from a discovered logo.

Used as corroborating branding evidence for sites whose CSS contains generic
framework colors (toast green, bootstrap blue, warning yellow, etc.).
"""
from __future__ import annotations

from io import BytesIO
import colorsys
from typing import Optional

import httpx
from PIL import Image

from app.services.ssrf_guard import validate_url


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#%02X%02X%02X" % rgb


def _distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return sum((x-y) ** 2 for x, y in zip(a, b)) ** 0.5


def extract_logo_palette(url: str, max_bytes: int = 2_500_000) -> list[str]:
    """Return up to 3 distinct chromatic colors from a public logo image."""
    try:
        safe = validate_url(url)
        with httpx.Client(timeout=8.0, follow_redirects=True) as client:
            r = client.get(safe, headers={"User-Agent": "EmbedIQ-BrandBot/1.0"})
            r.raise_for_status()
            if len(r.content) > max_bytes:
                return []
            ctype = r.headers.get("content-type", "")
            if "image" not in ctype.lower():
                return []

        image = Image.open(BytesIO(r.content)).convert("RGBA")
        image.thumbnail((240, 240))
        opaque = Image.new("RGBA", image.size, (255, 255, 255, 255))
        opaque.alpha_composite(image)
        rgb_img = opaque.convert("RGB").quantize(colors=24).convert("RGB")
        colors = rgb_img.getcolors(maxcolors=240*240) or []
        colors.sort(reverse=True, key=lambda item: item[0])

        candidates: list[tuple[int, tuple[int, int, int]]] = []
        for count, rgb in colors:
            r0, g0, b0 = rgb
            h, s, v = colorsys.rgb_to_hsv(r0/255, g0/255, b0/255)
            # Exclude white/black/gray wordmark pixels; keep actual brand accents.
            if s < 0.28 or v < 0.20 or v > 0.98:
                continue
            candidates.append((count, rgb))

        selected: list[tuple[int, int, int]] = []
        for _, rgb in candidates:
            if all(_distance(rgb, existing) >= 55 for existing in selected):
                selected.append(rgb)
            if len(selected) == 3:
                break
        return [_hex(c) for c in selected]
    except Exception:
        return []
