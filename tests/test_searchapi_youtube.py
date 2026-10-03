from datetime import datetime

import pytest

from searchapi_youtube import SearchApiError, SearchApiYouTube, parse_count, parse_relative_date


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload, self.status_code, self.ok = payload, status, status < 400

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, pages):
        self.pages, self.calls = list(pages), []

    def get(self, url, params, headers, timeout):
        self.calls.append(params)
        return self.pages.pop(0)


@pytest.mark.parametrize("raw, expected", [
    ("1.2M subscribers", 1_200_000), ("12,345 views", 12_345), ("3.4K", 3_400),
    (987, 987), ("No views", None), (None, None),
])
def test_parse_count(raw, expected):
    assert parse_count(raw) == expected


def test_parse_relative_date():
    now = datetime(2026, 10, 3)
    assert str(parse_relative_date("Streamed 2 weeks ago", now)) == "2026-09-19"
    assert str(parse_relative_date("5 hours ago", now)) == "2026-10-03"
    assert str(parse_relative_date("2024-01-15", now)) == "2024-01-15"
    assert parse_relative_date(None, now) is None


def test_fetch_channel_paginates_and_parses():
    session = FakeSession([
        FakeResponse({
            "channel": {"title": "Demo", "subscribers": "1.5K subscribers", "videos": "2 videos"},
            "videos": [{"id": "a", "title": "A", "views": "1,000 views", "published_time": "2024-01-02"}],
            "pagination": {"next_page_token": "tok"},
        }),
        FakeResponse({
            "videos": [{"id": "b", "title": "B", "views": "2K views", "published_time": "2024-01-01"}],
        }),
    ])
    channel, videos = SearchApiYouTube(api_key="k", session=session).fetch_channel("UC123")

    assert channel["TITLE"] == "Demo" and channel["SUBSCRIBERS"] == 1_500
    assert list(videos["VIDEO_ID"]) == ["b", "a"]  # sorted oldest first
    assert list(videos["VIEWS"]) == [2_000, 1_000]
    assert session.calls[0] == {"engine": "youtube_channel", "channel_id": "UC123"}
    assert session.calls[1]["next_page_token"] == "tok"


def test_error_payload_raises():
    session = FakeSession([FakeResponse({"error": "Invalid API key"}, status=401)])
    with pytest.raises(SearchApiError, match="Invalid API key"):
        SearchApiYouTube(api_key="bad", session=session).search("youtube_channel", channel_id="x")


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("SEARCHAPI_API_KEY", raising=False)
    with pytest.raises(SearchApiError):
        SearchApiYouTube()
