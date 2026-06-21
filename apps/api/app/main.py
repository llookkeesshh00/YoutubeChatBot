from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.models import ChatIn, ChatOut, Citation, TranscriptCreated, TranscriptIn, YouTubeImportIn
from app.services.hf_client import answer_with_context
from app.services.retrieval import RagIndex
from app.services.youtube import (
    YouTubeTranscriptError,
    extract_video_id,
    fetch_youtube_transcript,
)


settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class TranscriptSession:
    title: str
    source_url: str | None
    transcript: str
    index: RagIndex
    video_id: str | None = None


SESSIONS: dict[str, TranscriptSession] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.post("/api/transcripts", response_model=TranscriptCreated)
def create_transcript(payload: TranscriptIn) -> TranscriptCreated:
    return _create_session(
        title=payload.title,
        source_url=payload.source_url,
        transcript=payload.transcript,
        source_label=payload.source_url or "manual-transcript",
    )


@app.post("/api/youtube/import", response_model=TranscriptCreated)
def import_youtube(payload: YouTubeImportIn) -> TranscriptCreated:
    try:
        video_id = extract_video_id(payload.url)
        print(f"[youtube] Fetching transcript for video_id={video_id}.", flush=True)
        transcript = fetch_youtube_transcript(video_id)
    except YouTubeTranscriptError as exc:
        print(f"[youtube] Import failed: {exc}", flush=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    title = payload.title or f"YouTube video {video_id}"
    return _create_session(
        title=title,
        source_url=payload.url,
        transcript=transcript,
        source_label=f"youtube:{video_id}",
        video_id=video_id,
    )


@app.post("/api/chat", response_model=ChatOut)
async def chat(payload: ChatIn) -> ChatOut:
    started_at = perf_counter()
    print(
        f"[chat] Received question session={payload.session_id} "
        f"message='{_preview(payload.message)}'",
        flush=True,
    )

    session = SESSIONS.get(payload.session_id)
    if session is None:
        print(f"[chat] Session not found: {payload.session_id}", flush=True)
        raise HTTPException(status_code=404, detail="Transcript session not found.")

    results = session.index.search(payload.message)
    result_summary = ", ".join(
        f"{result.chunk_id}:{result.score:.3f}" for result in results
    )
    print(
        f"[chat] Retrieved {len(results)} chunks for session={payload.session_id}: "
        f"{result_summary or 'none'}",
        flush=True,
    )

    context_blocks = [_format_context(result) for result in results]
    answer = await answer_with_context(payload.message, context_blocks)
    elapsed_ms = int((perf_counter() - started_at) * 1000)
    print(
        f"[chat] Assistant answer ready in {elapsed_ms}ms: '{_preview(answer)}'",
        flush=True,
    )

    return ChatOut(
        answer=answer,
        citations=[
            Citation(
                chunk_id=result.chunk_id,
                text=result.text,
                start_seconds=None,
                end_seconds=None,
                timestamp=None,
            )
            for result in results
        ],
    )


def _create_session(
    title: str,
    source_url: str | None,
    transcript: str,
    source_label: str,
    video_id: str | None = None,
) -> TranscriptCreated:
    session_id = str(uuid4())
    print(f"[rag] Creating FAISS session {session_id} from source={source_label}.", flush=True)
    index = RagIndex(transcript=transcript, source=source_label)
    SESSIONS[session_id] = TranscriptSession(
        title=title,
        source_url=source_url,
        transcript=transcript,
        index=index,
        video_id=video_id,
    )
    print(
        f"[rag] Created session {session_id} with {index.chunks_count} FAISS chunks.",
        flush=True,
    )
    return TranscriptCreated(
        session_id=session_id,
        title=title,
        chunks_count=index.chunks_count,
        source_url=source_url,
        video_id=video_id,
    )


def _format_context(result) -> str:
    return f"[{result.chunk_id}] {result.text}"


def _preview(value: str, limit: int = 180) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit]}..."
