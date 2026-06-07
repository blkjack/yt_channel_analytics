"""Load and normalise configuration."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

# Project root = the faceless_shorts/ directory (parent of this package).
ROOT = Path(__file__).resolve().parent.parent

DEFAULTS = {
    "channel": {"name": "Daily Motivation", "handle": "@dailymotivation"},
    "video": {
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "lead_in": 0.6,
        "tail": 1.8,
        "max_duration": 58,
    },
    "tts": {
        "engine": "auto",
        "edge_voice": "en-US-GuyNeural",
        "edge_rate": "-8%",
        "espeak_voice": "en-us+m3",
        "espeak_speed": 145,
    },
    "text": {
        "font": "",
        "author_font": "",
        "max_font_size": 100,
        "min_font_size": 46,
        "color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 7,
        "show_quote_marks": True,
    },
    "background": {
        "mode": "auto",
        "videos_dir": "assets/backgrounds",
        "music_dir": "assets/music",
        "music_volume": 0.12,
        "overlay_darken": 0.42,
        "vignette": True,
    },
    "quotes": {
        "source": "local",
        "bank": "assets/quotes.json",
        "avoid_repeats_file": "output/.used_quotes.json",
    },
    "upload": {
        "privacy": "private",
        "category_id": "22",
        "client_secret": "secrets/client_secret.json",
        "token": "secrets/token.json",
        "default_hashtags": ["#Shorts", "#motivation", "#inspiration"],
    },
    "output_dir": "output",
}

# System font fallback that ships with most Linux images (and this container).
FALLBACK_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


class Config:
    def __init__(self, data: dict):
        self._d = data

    def __getitem__(self, key):
        return self._d[key]

    def get(self, key, default=None):
        return self._d.get(key, default)

    def path(self, relative: str) -> Path:
        """Resolve a path from config relative to the project root."""
        p = Path(relative)
        return p if p.is_absolute() else (ROOT / p)

    def font_path(self, which: str = "font") -> str:
        configured = self._d["text"].get(which) or ""
        if configured:
            return str(self.path(configured))
        if os.path.exists(FALLBACK_FONT):
            return FALLBACK_FONT
        raise FileNotFoundError(
            "No font found. Set text.font in config.yaml to a .ttf path."
        )

    @property
    def raw(self) -> dict:
        return self._d


def load_config(path: str | None = None) -> Config:
    cfg_path = Path(path) if path else (ROOT / "config.yaml")
    user = {}
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            user = yaml.safe_load(f) or {}
    merged = _deep_merge(DEFAULTS, user)
    return Config(merged)
