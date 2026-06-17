from dataclasses import dataclass
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.models import ChatIn, ChatOut, Citation, TranscriptCreated, TranscriptIn
from app.services.hf_client import answer_with_context
from app.services.retrieval import RagIndex
from app.services.transcripts import TranscriptChunk, chunk_transcript, format_timestamp


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
    chunks: list[TranscriptChunk]
    index: RagIndex


SESSIONS: dict[str, TranscriptSession] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.post("/api/transcripts", response_model=TranscriptCreated)
def create_transcript(payload: TranscriptIn) -> TranscriptCreated:
    chunks = chunk_transcript(payload.transcript)
    if not chunks:
        raise HTTPException(status_code=400, detail="Transcript did not produce chunks.")

    session_id = str(uuid4())
    SESSIONS[session_id] = TranscriptSession(
        title=payload.title,
        source_url=payload.source_url,
        chunks=chunks,
        index=RagIndex(chunks),
    )

    return TranscriptCreated(
        session_id=session_id,
        title=payload.title,
        chunks_count=len(chunks),
    )


@app.post("/api/chat", response_model=ChatOut)
async def chat(payload: ChatIn) -> ChatOut:
    session = SESSIONS.get(payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Transcript session not found.")

    results = session.index.search(payload.message)
    context_blocks = [_format_context(result.chunk) for result in results]
    answer = await answer_with_context(payload.message, context_blocks)

    return ChatOut(
        answer=answer,
        citations=[
            Citation(
                chunk_id=result.chunk.id,
                text=result.chunk.text,
                start_seconds=result.chunk.start_seconds,
                end_seconds=result.chunk.end_seconds,
                timestamp=format_timestamp(result.chunk.start_seconds),
            )
            for result in results
        ],
    )


def _format_context(chunk: TranscriptChunk) -> str:
    timestamp = format_timestamp(chunk.start_seconds)
    if timestamp:
        return f"[{timestamp}] {chunk.text}"
    return chunk.text

