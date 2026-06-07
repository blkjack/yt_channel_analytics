"""Upload a generated short to YouTube via the (free) YouTube Data API v3."""
from __future__ import annotations

import json
from pathlib import Path

from .config import Config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_credentials(cfg: Config):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_secret = cfg.path(cfg["upload"]["client_secret"])
    token_path = cfg.path(cfg["upload"]["token"])

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_secret.exists():
                raise FileNotFoundError(
                    f"Missing OAuth client secret at {client_secret}.\n"
                    "See faceless_shorts/README.md -> 'YouTube upload setup'."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def upload_video(cfg: Config, video_path: Path, meta_path: Path) -> str:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
    creds = _get_credentials(cfg)
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta.get("tags", []),
            "categoryId": meta.get("categoryId", "22"),
        },
        "status": {
            "privacyStatus": meta.get("privacyStatus", "private"),
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True,
                            mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  [upload] {int(status.progress() * 100)}%")

    vid = response["id"]
    print(f"  [upload] done -> https://youtu.be/{vid} ({meta.get('privacyStatus')})")
    return vid
