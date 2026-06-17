from pydantic import BaseModel, Field


class TranscriptIn(BaseModel):
    title: str = Field(default="Untitled video", max_length=160)
    source_url: str | None = None
    transcript: str = Field(min_length=20)


class TranscriptCreated(BaseModel):
    session_id: str
    title: str
    chunks_count: int


class ChatIn(BaseModel):
    session_id: str
    message: str = Field(min_length=2, max_length=1000)


class Citation(BaseModel):
    chunk_id: str
    text: str
    start_seconds: float | None = None
    end_seconds: float | None = None
    timestamp: str | None = None


class ChatOut(BaseModel):
    answer: str
    citations: list[Citation]

