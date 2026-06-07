"""Text-to-speech with an online (edge-tts) primary and offline (espeak-ng) fallback."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .config import Config


class TTSError(RuntimeError):
    pass


def _have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _edge_tts(text: str, out_mp3: Path, voice: str, rate: str) -> None:
    if not _have("edge-tts"):
        raise TTSError("edge-tts not installed (pip install edge-tts)")
    # Use --opt=value form: rate/pitch values start with '-' (e.g. "-8%") and
    # argparse would otherwise treat them as a new flag.
    cmd = [
        "edge-tts",
        f"--voice={voice}",
        f"--rate={rate}",
        f"--text={text}",
        f"--write-media={out_mp3}",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0 or not out_mp3.exists() or out_mp3.stat().st_size == 0:
        raise TTSError(f"edge-tts failed: {proc.stderr.strip()[:300]}")


def _espeak(text: str, out_wav: Path, voice: str, speed: int) -> None:
    if not _have("espeak-ng") and not _have("espeak"):
        raise TTSError("espeak-ng not installed (apt-get install espeak-ng)")
    binary = "espeak-ng" if _have("espeak-ng") else "espeak"
    cmd = [binary, "-v", voice, "-s", str(speed), "-p", "45", "-a", "190",
           "-w", str(out_wav), text]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0 or not out_wav.exists() or out_wav.stat().st_size == 0:
        raise TTSError(f"espeak failed: {proc.stderr.strip()[:300]}")


def synthesize(cfg: Config, text: str, out_dir: Path, stem: str) -> Path:
    """Generate speech audio for `text`. Returns the audio file path.

    Honours tts.engine = auto | edge | espeak.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    t = cfg["tts"]
    engine = t["engine"]

    mp3 = out_dir / f"{stem}.mp3"
    wav = out_dir / f"{stem}.wav"

    if engine in ("edge", "auto"):
        try:
            _edge_tts(text, mp3, t["edge_voice"], t["edge_rate"])
            return mp3
        except TTSError as e:
            if engine == "edge":
                raise
            print(f"  [tts] edge-tts unavailable ({e}); falling back to espeak-ng")

    _espeak(text, wav, t["espeak_voice"], int(t["espeak_speed"]))
    return wav


def audio_duration(path: Path) -> float:
    """Return audio duration in seconds via ffprobe."""
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(proc.stdout.strip())
    except ValueError:
        raise TTSError(f"could not probe duration of {path}: {proc.stderr[:200]}")
