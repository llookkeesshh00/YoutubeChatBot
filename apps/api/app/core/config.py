from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "YouTube Transcript Chatbot API"
    app_env: str = "local"
    web_origin: str = "http://localhost:3000"
    hf_token: str | None = None
    hf_model: str = "openai/gpt-oss-120b:fastest"
    hf_timeout_seconds: float = 20.0
    embedding_provider: str = "huggingface"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 4

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
