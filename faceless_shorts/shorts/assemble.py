"""Compose the final vertical MP4 with ffmpeg."""
from __future__ import annotations

import subprocess
from pathlib import Path

from .config import Config


class AssembleError(RuntimeError):
    pass


def compute_duration(cfg: Config, voice_dur: float) -> float:
    v = cfg["video"]
    dur = float(v["lead_in"]) + voice_dur + float(v["tail"])
    dur = max(3.0, min(dur, float(v["max_duration"])))
    return round(dur, 2)


def build_video(
    cfg: Config,
    background: dict,
    overlay_png: Path,
    voice_audio: Path,
    duration: float,
    out_path: Path,
    music: Path | None = None,
) -> Path:
    v = cfg["video"]
    bg = cfg["background"]
    W, H, FPS = int(v["width"]), int(v["height"]), int(v["fps"])
    darken = float(bg["overlay_darken"])
    lead_ms = int(float(v["lead_in"]) * 1000)

    inputs: list[str] = []

    # --- input 0: background ---
    if background["type"] == "video":
        inputs += ["-stream_loop", "-1", "-t", f"{duration}", "-i", str(background["path"])]
        bg_chain = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1"
    else:
        c0, c1 = background["palette"]
        grad = (f"gradients=s={W}x{H}:c0={c0}:c1={c1}:x0=0:y0=0:x1=0:y1={H}"
                f":type=linear:speed=0.012:duration=12")
        inputs += ["-f", "lavfi", "-t", f"{duration}", "-i", grad]
        bg_chain = f"[0:v]fps={FPS},setsar=1"

    bg_chain += f",drawbox=x=0:y=0:w={W}:h={H}:color=black@{darken}:t=fill"
    if bg.get("vignette"):
        bg_chain += ",vignette=PI/4.2"
    bg_chain += "[bg]"

    # --- input 1: overlay png ---
    inputs += ["-loop", "1", "-t", f"{duration}", "-i", str(overlay_png)]

    # --- input 2: voice ---
    inputs += ["-i", str(voice_audio)]

    # --- input 3: music (optional) ---
    has_music = music is not None
    if has_music:
        inputs += ["-i", str(music)]

    # --- filter graph ---
    parts = [
        bg_chain,
        "[1:v]format=rgba,fade=t=in:st=0.25:d=0.8:alpha=1[txt]",
        f"[bg][txt]overlay=0:0:format=auto[outv]",
        f"[2:a]adelay={lead_ms}|{lead_ms},apad[v0]",
    ]
    if has_music:
        mv = float(bg["music_volume"])
        fade_st = max(0.0, duration - 1.2)
        parts.append(
            f"[3:a]aloop=loop=-1:size=2000000000,volume={mv},"
            f"afade=t=out:st={fade_st}:d=1.2[m0]"
        )
        parts.append("[v0][m0]amix=inputs=2:duration=first:normalize=0[outa]")
        a_out = "[outa]"
    else:
        a_out = "[v0]"

    filter_complex = ";".join(parts)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", a_out,
            "-t", f"{duration}",
            "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(out_path),
        ]
    )

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out_path.exists():
        raise AssembleError(
            "ffmpeg failed:\n" + proc.stderr[-1500:]
        )
    return out_path
