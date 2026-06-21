import re
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi

from app.services.transcripts import format_timestamp


VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")
DEFAULT_LANGUAGES = ["en", "en-US", "en-GB"]


class YouTubeTranscriptError(RuntimeError):
    pass


def extract_video_id(value: str) -> str:
    candidate = value.strip()
    if VIDEO_ID_RE.match(candidate):
        return candidate

    parsed = urlparse(candidate)
    host = parsed.netloc.lower()

    if "youtu.be" in host:
        video_id = parsed.path.strip("/").split("/")[0]
        if VIDEO_ID_RE.match(video_id):
            return video_id

    if "youtube.com" in host:
        query_id = parse_qs(parsed.query).get("v", [None])[0]
        if query_id and VIDEO_ID_RE.match(query_id):
            return query_id

        parts = [part for part in parsed.path.split("/") if part]
        for marker in ("shorts", "embed", "live"):
            if marker in parts:
                index = parts.index(marker)
                if index + 1 < len(parts) and VIDEO_ID_RE.match(parts[index + 1]):
                    return parts[index + 1]

    raise YouTubeTranscriptError("Could not extract a valid YouTube video ID.")


def fetch_youtube_transcript(video_id: str, languages: list[str] | None = None) -> str:
    requested_languages = languages or DEFAULT_LANGUAGES
    try:
        transcript_items = _fetch_transcript_items(video_id, requested_languages)
    except Exception as exc:
        error_name = exc.__class__.__name__
        raise YouTubeTranscriptError(
            f"Could not fetch captions for this video ({error_name}): {exc}"
        ) from exc

    lines = []
    for item in transcript_items:
        start = _read_float(item, "start", 0)
        timestamp = format_timestamp(start)
        text = str(_read_value(item, "text", "")).replace("\n", " ").strip()
        if text:
            lines.append(f"[{timestamp}] {text}")

    if not lines:
        raise YouTubeTranscriptError("Captions were found, but they were empty.")

    print(
        f"[youtube] Fetched {len(lines)} caption snippets for video_id={video_id}.",
        flush=True,
    )
    return " ".join(lines)


def _fetch_transcript_items(video_id: str, languages: list[str]):
    api = YouTubeTranscriptApi()

    if hasattr(api, "fetch"):
        fetched = api.fetch(video_id, languages=languages)
        if hasattr(fetched, "to_raw_data"):
            return fetched.to_raw_data()
        return list(fetched)

    if hasattr(YouTubeTranscriptApi, "get_transcript"):
        return YouTubeTranscriptApi.get_transcript(video_id, languages=languages)

    raise YouTubeTranscriptError("Installed youtube-transcript-api version has no supported fetch method.")


def _read_value(item, key: str, default):
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _read_float(item, key: str, default: float) -> float:
    try:
        return float(_read_value(item, key, default))
    except (TypeError, ValueError):
        return default
