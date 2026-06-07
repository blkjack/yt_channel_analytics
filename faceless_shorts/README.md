# Faceless Shorts — automated motivational YouTube channel

A **100% free**, fully scriptable pipeline that turns motivational quotes into
ready-to-publish vertical **YouTube Shorts** — voiceover, animated background,
on-screen text, metadata, and (optionally) automatic upload.

No paid APIs required. Optional upgrades (`edge-tts` neural voices, online quote
API, YouTube auto-upload) are all free too.

```
quote  ->  voiceover  ->  background + text  ->  MP4  ->  metadata  ->  YouTube
```

---

## How it relates to `Open-Generative-AI`

[`Open-Generative-AI`](https://github.com/Anil-matcha/Open-Generative-AI) is a
self-hosted **media-generation studio** (image / video / lip-sync) that calls
the paid **Muapi.ai** gateway. It's a great *visuals engine* but has no
scripting, TTS, captioning, scheduling or uploading. This project is the
**automation layer** around those steps. If you later want AI-generated cinematic
backgrounds, render clips in Open-GenAI and drop them into
`assets/backgrounds/` — the pipeline will use them automatically.

---

## Quick start

```bash
cd faceless_shorts

# 1. System deps (one time)
sudo apt-get install -y ffmpeg espeak-ng        # macOS: brew install ffmpeg espeak-ng

# 2. Python deps
pip install -r requirements.txt

# 3. Make a video (writes to output/)
python make_short.py

# Make 5 at once:
python make_short.py --count 5
```

Each run produces `output/short_<timestamp>.mp4` plus a matching `.json` with the
title/description/tags.

---

## Configuration

Everything is in **`config.yaml`** — channel name, voice, fonts, colours,
background mode, music volume, upload privacy. Sensible defaults are built in, so
you can run it without editing anything.

Highlights:

| Setting | What it does |
|---|---|
| `tts.engine` | `auto` (edge-tts → espeak fallback), `edge`, or `espeak` |
| `tts.edge_voice` | neural voice, e.g. `en-US-GuyNeural`, `en-US-AriaNeural` |
| `background.mode` | `auto` (use your clips if present, else gradient), `gradient`, `video` |
| `background.music_volume` | `0` = silent; otherwise music ducked under voice |
| `quotes.source` | `local` (bundled bank) or `zenquotes` (free online API) |
| `upload.privacy` | `private` / `unlisted` / `public` — **start with `private`!** |

### Voices, backgrounds, music
- **Voice:** `edge-tts` gives free, natural neural voices (needs internet).
  Offline it falls back to `espeak-ng` (robotic — fine for testing).
- **Backgrounds:** drop free loop clips into `assets/backgrounds/` (see that
  folder's README for sources). Empty = animated gradient, zero assets needed.
- **Music:** drop royalty-free tracks into `assets/music/`.

### Quotes
- Default: the bundled `assets/quotes.json` (~60 quotes; recently-used ones are
  remembered to avoid repeats).
- Add your own by editing that file (`{"text": "...", "author": "..."}`).
- Or set `quotes.source: zenquotes` for an endless free supply online.

---

## YouTube upload setup (free)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) → create a
   project → **enable the "YouTube Data API v3"**.
2. **OAuth consent screen** → External → add your Google account as a *Test user*.
3. **Credentials** → Create credentials → **OAuth client ID** → *Desktop app* →
   download the JSON.
4. Save it as `faceless_shorts/secrets/client_secret.json`.
5. First upload triggers a browser login (token cached to `secrets/token.json`):

```bash
python make_short.py --upload          # generate + upload
python upload_short.py --latest        # upload the newest existing video
```

> The YouTube API has a daily quota (~6 uploads/day on the default quota) — plenty
> for one channel. Keep `upload.privacy: private` until you've reviewed a few.

---

## Full automation (set-and-forget)

**Option A — cron (your own machine/server):**
```cron
0 13 * * *  cd /path/to/faceless_shorts && python make_short.py --upload >> cron.log 2>&1
```

**Option B — GitHub Actions:** see `deploy/daily.yml` for a ready-made daily
workflow (instructions in the file header).

---

## Project layout

```
faceless_shorts/
├── config.yaml          # ← edit me
├── make_short.py        # generate videos
├── upload_short.py      # upload to YouTube
├── assets/quotes.json   # quote bank
├── assets/backgrounds/  # optional loop clips
├── assets/music/        # optional music
├── shorts/              # pipeline: quotes, tts, text_render, background,
│                        #           assemble, metadata, upload, pipeline
└── deploy/daily.yml     # optional GitHub Actions scheduler
```

## Troubleshooting
- **`ffmpeg: not found`** → install it (see Quick start).
- **edge-tts SSL/connection errors** → behind a TLS-proxy? It falls back to
  espeak automatically when `tts.engine: auto`.
- **Upload 403 / quota** → enable the API, add yourself as a Test user, and check
  your daily upload quota.
