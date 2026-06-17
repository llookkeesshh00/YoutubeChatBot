from dataclasses import dataclass
import re


TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}(?::\d{2})?(?:[,.]\d{1,3})?)\s*-->\s*"
    r"(?P<end>\d{1,2}:\d{2}(?::\d{2})?(?:[,.]\d{1,3})?)"
)


@dataclass(frozen=True)
class TranscriptChunk:
    id: str
    text: str
    start_seconds: float | None = None
    end_seconds: float | None = None


def normalize_transcript(raw: str) -> str:
    lines = []
    for line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        stripped = line.strip()
        if not stripped or stripped.upper() == "WEBVTT":
            continue
        if stripped.isdigit():
            continue
        lines.append(stripped)
    return "\n".join(lines)


def chunk_transcript(raw: str, target_words: int = 180) -> list[TranscriptChunk]:
    normalized = normalize_transcript(raw)
    timed_segments = _parse_timed_segments(normalized)

    if timed_segments:
        return _merge_timed_segments(timed_segments, target_words)

    return _chunk_plain_text(normalized, target_words)


def format_timestamp(seconds: float | None) -> str | None:
    if seconds is None:
        return None

    whole = int(seconds)
    hours = whole // 3600
    minutes = (whole % 3600) // 60
    secs = whole % 60

    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _parse_timed_segments(text: str) -> list[TranscriptChunk]:
    segments: list[TranscriptChunk] = []
    current_start: float | None = None
    current_end: float | None = None
    current_lines: list[str] = []

    for line in text.split("\n"):
        match = TIMESTAMP_RE.search(line)
        if match:
            if current_lines:
                segments.append(
                    TranscriptChunk(
                        id=f"segment-{len(segments) + 1}",
                        text=" ".join(current_lines).strip(),
                        start_seconds=current_start,
                        end_seconds=current_end,
                    )
                )
                current_lines = []

            current_start = _timestamp_to_seconds(match.group("start"))
            current_end = _timestamp_to_seconds(match.group("end"))
            continue

        if line.strip():
            current_lines.append(line.strip())

    if current_lines:
        segments.append(
            TranscriptChunk(
                id=f"segment-{len(segments) + 1}",
                text=" ".join(current_lines).strip(),
                start_seconds=current_start,
                end_seconds=current_end,
            )
        )

    return [segment for segment in segments if segment.text]


def _merge_timed_segments(
    segments: list[TranscriptChunk], target_words: int
) -> list[TranscriptChunk]:
    chunks: list[TranscriptChunk] = []
    bucket: list[str] = []
    start: float | None = None
    end: float | None = None

    for segment in segments:
        if start is None:
            start = segment.start_seconds
        end = segment.end_seconds
        bucket.append(segment.text)

        if len(" ".join(bucket).split()) >= target_words:
            chunks.append(
                TranscriptChunk(
                    id=f"chunk-{len(chunks) + 1}",
                    text=" ".join(bucket).strip(),
                    start_seconds=start,
                    end_seconds=end,
                )
            )
            bucket = []
            start = None
            end = None

    if bucket:
        chunks.append(
            TranscriptChunk(
                id=f"chunk-{len(chunks) + 1}",
                text=" ".join(bucket).strip(),
                start_seconds=start,
                end_seconds=end,
            )
        )

    return chunks


def _chunk_plain_text(text: str, target_words: int) -> list[TranscriptChunk]:
    words = text.replace("\n", " ").split()
    chunks: list[TranscriptChunk] = []

    for index in range(0, len(words), target_words):
        chunk_words = words[index : index + target_words]
        if chunk_words:
            chunks.append(
                TranscriptChunk(
                    id=f"chunk-{len(chunks) + 1}",
                    text=" ".join(chunk_words),
                )
            )

    return chunks


def _timestamp_to_seconds(value: str) -> float:
    clean = value.replace(",", ".")
    parts = clean.split(":")

    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)

    hours, minutes, seconds = parts
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

