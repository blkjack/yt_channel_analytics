#!/usr/bin/env python3
"""Generate one or more faceless motivational Shorts.

Examples:
    python make_short.py                       # one video into output/
    python make_short.py --count 5            # five videos
    python make_short.py --quote "Stay hungry - Steve Jobs"
    python make_short.py --upload             # generate AND upload to YouTube
"""
from __future__ import annotations

import argparse
import sys

from shorts.config import load_config
from shorts.pipeline import generate_short


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate faceless motivational Shorts")
    ap.add_argument("--config", default=None, help="path to config.yaml")
    ap.add_argument("--count", type=int, default=1, help="number of videos to make")
    ap.add_argument("--quote", default=None, help='force a quote: "Text - Author"')
    ap.add_argument("--upload", action="store_true", help="upload each video after making it")
    args = ap.parse_args()

    cfg = load_config(args.config)
    results = []
    for i in range(args.count):
        print(f"\n=== Short {i + 1}/{args.count} ===")
        try:
            res = generate_short(cfg, explicit_quote=args.quote)
            results.append(res)
        except Exception as e:
            print(f"  [error] {e}", file=sys.stderr)
            return 1

        if args.upload:
            from shorts.upload import upload_video
            upload_video(cfg, res["video"], res["metadata"])

    print(f"\nDone. {len(results)} video(s) in {cfg.path(cfg['output_dir'])}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
