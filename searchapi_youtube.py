"""Fetch live, public YouTube channel data through SearchApi (https://www.searchapi.io).

The bundled CSV only covers one synthetic channel. This module lets the app
pull real public data for any channel via SearchApi's ``youtube_channel``
engine, without YouTube Data API quotas or OAuth.

Usage:
    export SEARCHAPI_API_KEY=...
    from searchapi_youtube import SearchApiYouTube
    client = SearchApiYouTube()
    channel, videos = client.fetch_channel("UCxxxxxxxxxxxxxxxxxxxxxx")
"""

import os
import re
from datetime import datetime, timedelta

import pandas as pd
import requests

SEARCHAPI_URL = "https://www.searchapi.io/api/v1/search"

_SUFFIXES = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
_UNIT_DAYS = {
    "second": 0, "minute": 0, "hour": 0, "day": 1,
    "week": 7, "month": 30, "year": 365,
}


class SearchApiError(RuntimeError):
    """Raised when SearchApi returns an error payload or a non-2xx status."""


def parse_count(value):
    """Turn '1.2M subscribers', '12,345 views' or 987 into an int (None if unknown)."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"([\d.,]+)\s*([KMB])?", str(value).upper())
    if not match:
        return None
    number = float(match.group(1).replace(",", ""))
    return int(round(number * _SUFFIXES.get(match.group(2), 1)))


def parse_relative_date(value, now=None):
    """Approximate a date from YouTube's relative strings, e.g. 'Streamed 3 weeks ago'."""
    if not value:
        return None
    now = now or datetime.now()
    match = re.search(r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", str(value).lower())
    if match:
        return (now - timedelta(days=int(match.group(1)) * _UNIT_DAYS[match.group(2)])).date()
    try:
        return pd.to_datetime(value).date()
    except (ValueError, TypeError):
        return None


class SearchApiYouTube:
    """Minimal client for SearchApi's YouTube channel engine."""

    def __init__(self, api_key=None, session=None, timeout=30):
        self.api_key = api_key or os.environ.get("SEARCHAPI_API_KEY")
        if not self.api_key:
            raise SearchApiError("Set SEARCHAPI_API_KEY or pass api_key (get one at https://www.searchapi.io).")
        self.session = session or requests.Session()
        self.timeout = timeout

    def search(self, engine, **params):
        response = self.session.get(
            SEARCHAPI_URL,
            params={"engine": engine, **params},
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if not response.ok or "error" in payload:
            raise SearchApiError(payload.get("error") or f"HTTP {response.status_code}")
        return payload

    def fetch_channel(self, channel_id, max_pages=5):
        """Return (channel_info dict, videos DataFrame) for a channel ID."""
        params = {"channel_id": channel_id}
        channel, videos = {}, []
        for _ in range(max_pages):
            payload = self.search("youtube_channel", **params)
            channel = channel or payload.get("channel", {})
            videos.extend(payload.get("videos", []))
            token = (payload.get("pagination") or {}).get("next_page_token")
            if not token:
                break
            params = {"channel_id": channel_id, "next_page_token": token}
        return self._channel_info(channel), self._videos_frame(videos)

    @staticmethod
    def _channel_info(channel):
        return {
            "TITLE": channel.get("title"),
            "HANDLE": channel.get("handle"),
            "SUBSCRIBERS": parse_count(channel.get("subscribers")),
            "VIDEOS": parse_count(channel.get("videos")),
            "LINK": channel.get("link"),
        }

    @staticmethod
    def _videos_frame(videos):
        rows = [{
            "TITLE": v.get("title"),
            "VIDEO_ID": v.get("id"),
            "LINK": v.get("link"),
            "VIEWS": parse_count(v.get("views")),
            "PUBLISHED": parse_relative_date(v.get("published_time")),
            "LENGTH": v.get("length"),
        } for v in videos]
        df = pd.DataFrame(rows, columns=["TITLE", "VIDEO_ID", "LINK", "VIEWS", "PUBLISHED", "LENGTH"])
        df["PUBLISHED"] = pd.to_datetime(df["PUBLISHED"])
        return df.drop_duplicates("VIDEO_ID").sort_values("PUBLISHED").reset_index(drop=True)
