"""End-to-end: quote -> voice -> visuals -> MP4 + metadata."""
from __future__ import annotations

import time
from pathlib import Path

from .assemble import build_video, compute_duration
from .background import pick_background, pick_music
from .config import Config
from .metadata import build_metadata, save_metadata
from .quotes import pick_quote
from .text_render import render_quote_png
from .tts import audio_duration, synthesize


def generate_short(cfg: Config, explicit_quote: str | None = None) -> dict:
    out_dir = cfg.path(cfg["output_dir"])
    work = out_dir / "work"
    work.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    stem = f"short_{stamp}"

    # 1. Quote
    quote = pick_quote(cfg, explicit=explicit_quote)
    print(f"  [quote] \"{quote['text']}\" — {quote.get('author','')}")

    # 2. Voiceover
    speech_text = quote["text"]
    if quote.get("author") and quote["author"].lower() != "unknown":
        speech_text = f"{quote['text']} ... {quote['author']}"
    voice = synthesize(cfg, speech_text, work, stem)
    voice_dur = audio_duration(voice)
    duration = compute_duration(cfg, voice_dur)
    print(f"  [tts]   {voice.name}  ({voice_dur:.1f}s voice -> {duration:.1f}s video)")

    # 3. Text overlay
    overlay = render_quote_png(cfg, quote, work / f"{stem}_overlay.png")

    # 4. Background + music
    bg = pick_background(cfg)
    music = pick_music(cfg)
    bg_desc = bg["path"].name if bg["type"] == "video" else f"gradient {bg['palette']}"
    print(f"  [bg]    {bg_desc}" + (f"  + music {music.name}" if music else ""))

    # 5. Assemble
    video_path = out_dir / f"{stem}.mp4"
    build_video(cfg, bg, overlay, voice, duration, video_path, music=music)
    print(f"  [video] {video_path}")

    # 6. Metadata
    meta = build_metadata(cfg, quote)
    meta_path = out_dir / f"{stem}.json"
    save_metadata(meta, meta_path)

    return {"video": video_path, "metadata": meta_path, "meta": meta, "duration": duration}
