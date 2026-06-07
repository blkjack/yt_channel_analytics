"""Render the quote (and author + handle) onto a transparent full-frame PNG."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import Config


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


def _wrap(draw, text, font, max_width) -> list[str]:
    words = text.split()
    lines, line = [], ""
    for w in words:
        trial = f"{line} {w}".strip()
        if draw.textlength(trial, font=font) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def _fit_font(draw, text, font_path, max_w, max_h, hi, lo):
    """Largest font size (between lo and hi) whose wrapped block fits the box."""
    best = lo
    best_lines = None
    size = hi
    while size >= lo:
        font = ImageFont.truetype(font_path, size)
        lines = _wrap(draw, text, font, max_w)
        ascent, descent = font.getmetrics()
        line_h = int((ascent + descent) * 1.18)
        total_h = line_h * len(lines)
        widest = max((draw.textlength(ln, font=font) for ln in lines), default=0)
        if total_h <= max_h and widest <= max_w:
            return font, lines, line_h
        best, best_lines = size, lines  # remember smallest attempt
        size -= 4
    font = ImageFont.truetype(font_path, lo)
    return font, _wrap(draw, text, font, max_w), int(sum(font.getmetrics()) * 1.18)


def render_quote_png(cfg: Config, quote: dict, out_path: Path) -> Path:
    W = cfg["video"]["width"]
    H = cfg["video"]["height"]
    t = cfg["text"]

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = int(W * 0.11)
    max_w = W - 2 * margin
    max_h = int(H * 0.52)

    font_path = cfg.font_path("font")
    author_font_path = cfg.font_path("author_font") if t.get("author_font") else font_path

    fill = _hex(t["color"])
    stroke = _hex(t["stroke_color"])
    stroke_w = int(t["stroke_width"])

    text = quote["text"].strip().strip('"')
    if t.get("show_quote_marks"):
        text = f"“{text}”"

    font, lines, line_h = _fit_font(
        draw, text, font_path, max_w, max_h,
        int(t["max_font_size"]), int(t["min_font_size"]),
    )

    block_h = line_h * len(lines)
    y = (H - block_h) // 2 - int(H * 0.02)

    for ln in lines:
        w = draw.textlength(ln, font=font)
        x = (W - w) / 2
        draw.text((x, y), ln, font=font, fill=fill,
                  stroke_width=stroke_w, stroke_fill=stroke)
        y += line_h

    # Author line
    author = (quote.get("author") or "").strip()
    if author and author.lower() != "unknown":
        a_size = max(int(font.size * 0.5), 34)
        a_font = ImageFont.truetype(author_font_path, a_size)
        a_text = f"— {author}"
        aw = draw.textlength(a_text, font=a_font)
        ay = y + int(line_h * 0.4)
        draw.text(((W - aw) / 2, ay), a_text, font=a_font, fill=fill,
                  stroke_width=max(2, stroke_w - 3), stroke_fill=stroke)

    # Channel handle watermark
    handle = (cfg["channel"].get("handle") or "").strip()
    if handle:
        h_font = ImageFont.truetype(font_path, 40)
        hw = draw.textlength(handle, font=h_font)
        draw.text(((W - hw) / 2, H - int(H * 0.085)), handle, font=h_font,
                  fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path
