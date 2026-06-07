"""Choose a background source (user video or generated gradient) and music."""
from __future__ import annotations

import random
from pathlib import Path

from .config import Config

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}

# Cinematic two-colour gradient palettes (hex pairs, top -> bottom-ish).
GRADIENT_PALETTES = [
    ("0x0f2027", "0x2c5364"),  # deep teal
    ("0x232526", "0x414345"),  # graphite
    ("0x1a2a6c", "0xb21f1f"),  # midnight to crimson
    ("0x141e30", "0x243b55"),  # navy steel
    ("0x000428", "0x004e92"),  # blue depths
    ("0x42275a", "0x734b6d"),  # dusk purple
    ("0x0b486b", "0xf56217"),  # ocean sunset
    ("0x16222a", "0x3a6073"),  # slate
    ("0x355c7d", "0x6c5b7b"),  # twilight
    ("0x232526", "0x1c1c1c"),  # near black
]


def pick_background(cfg: Config) -> dict:
    bg = cfg["background"]
    mode = bg["mode"]
    videos_dir = cfg.path(bg["videos_dir"])

    videos = []
    if videos_dir.exists():
        videos = [p for p in sorted(videos_dir.iterdir())
                  if p.suffix.lower() in VIDEO_EXTS]

    if mode == "video":
        if not videos:
            raise FileNotFoundError(
                f"background.mode='video' but no videos in {videos_dir}"
            )
        return {"type": "video", "path": random.choice(videos)}

    if mode == "auto" and videos:
        return {"type": "video", "path": random.choice(videos)}

    # gradient
    return {"type": "gradient", "palette": random.choice(GRADIENT_PALETTES)}


def pick_music(cfg: Config) -> Path | None:
    bg = cfg["background"]
    if float(bg.get("music_volume", 0)) <= 0:
        return None
    music_dir = cfg.path(bg["music_dir"])
    if not music_dir.exists():
        return None
    tracks = [p for p in sorted(music_dir.iterdir())
              if p.suffix.lower() in AUDIO_EXTS]
    return random.choice(tracks) if tracks else None
