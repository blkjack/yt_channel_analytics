#!/usr/bin/env python3
"""Upload an already-generated short to YouTube.

Examples:
    python upload_short.py output/short_20260607_120000.mp4
    python upload_short.py --latest          # upload the newest video in output/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from shorts.config import load_config
from shorts.upload import upload_video


def main() -> int:
    ap = argparse.ArgumentParser(description="Upload a short to YouTube")
    ap.add_argument("video", nargs="?", help="path to the .mp4 (omit with --latest)")
    ap.add_argument("--latest", action="store_true", help="upload newest video in output/")
    ap.add_argument("--config", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)

    if args.latest:
        out = cfg.path(cfg["output_dir"])
        vids = sorted(out.glob("short_*.mp4"))
        if not vids:
            print("No videos found in output/", file=sys.stderr)
            return 1
        video = vids[-1]
    elif args.video:
        video = Path(args.video)
    else:
        print("Provide a video path or --latest", file=sys.stderr)
        return 1

    meta = video.with_suffix(".json")
    if not meta.exists():
        print(f"Metadata file not found: {meta}", file=sys.stderr)
        return 1

    upload_video(cfg, video, meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
