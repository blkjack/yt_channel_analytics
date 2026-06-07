"""Build YouTube metadata (title, description, tags) for a quote short."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .config import Config


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().strip('"')


def build_metadata(cfg: Config, quote: dict) -> dict:
    text = _clean(quote["text"])
    author = (quote.get("author") or "").strip()
    hashtags = cfg["upload"].get("default_hashtags", ["#Shorts"])

    # Title: keep under ~90 chars, always include #Shorts so YouTube treats it as a Short.
    short_text = text if len(text) <= 70 else text[:67].rstrip() + "..."
    title = f"{short_text} 💪 #Shorts"
    if len(title) > 99:
        title = title[:96] + "..."

    by = f" — {author}" if author and author.lower() != "unknown" else ""
    description = (
        f"\"{text}\"{by}\n\n"
        f"{cfg['channel']['name']} — daily motivation to keep you moving forward.\n"
        f"Like & subscribe for a dose of inspiration every day.\n\n"
        + " ".join(hashtags)
    )

    base_tags = ["motivation", "motivational", "inspiration", "inspirational quotes",
                 "success", "mindset", "self improvement", "discipline", "shorts",
                 "daily motivation", "quotes"]
    if author and author.lower() != "unknown":
        base_tags.append(author.lower())

    return {
        "title": title,
        "description": description,
        "tags": base_tags[:15],
        "categoryId": str(cfg["upload"]["category_id"]),
        "privacyStatus": cfg["upload"]["privacy"],
        "quote": {"text": text, "author": author},
    }


def save_metadata(meta: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
