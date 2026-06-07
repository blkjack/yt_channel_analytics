"""Pick a quote from the local bank or a free online API."""
from __future__ import annotations

import json
import random
import urllib.request
from pathlib import Path

from .config import Config


def _load_bank(cfg: Config) -> list[dict]:
    bank_path = cfg.path(cfg["quotes"]["bank"])
    with open(bank_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [q for q in data if q.get("text")]


def _load_used(cfg: Config) -> list[str]:
    p = cfg.path(cfg["quotes"]["avoid_repeats_file"])
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_used(cfg: Config, used: list[str]) -> None:
    p = cfg.path(cfg["quotes"]["avoid_repeats_file"])
    p.parent.mkdir(parents=True, exist_ok=True)
    # keep only the most recent 200 to bound the file
    p.write_text(json.dumps(used[-200:], ensure_ascii=False, indent=0), encoding="utf-8")


def _fetch_zenquotes() -> dict | None:
    """Free, no-key quote API. Returns None on any failure."""
    try:
        req = urllib.request.Request(
            "https://zenquotes.io/api/random",
            headers={"User-Agent": "faceless-shorts/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        item = data[0]
        return {"text": item["q"].strip(), "author": item.get("a", "Unknown").strip()}
    except Exception:
        return None


def pick_quote(cfg: Config, explicit: str | None = None) -> dict:
    """Return a quote dict: {"text": ..., "author": ...}.

    `explicit` lets the caller force a specific quote string (author optional,
    using "Quote text - Author" syntax).
    """
    if explicit:
        if " - " in explicit:
            text, author = explicit.rsplit(" - ", 1)
        else:
            text, author = explicit, "Unknown"
        return {"text": text.strip(), "author": author.strip()}

    source = cfg["quotes"]["source"]
    if source == "zenquotes":
        q = _fetch_zenquotes()
        if q:
            return q
        # fall through to local bank if the API is unreachable

    bank = _load_bank(cfg)
    used = set(_load_used(cfg))
    candidates = [q for q in bank if q["text"] not in used] or bank
    chosen = random.choice(candidates)

    used_list = _load_used(cfg)
    used_list.append(chosen["text"])
    _save_used(cfg, used_list)
    return chosen
