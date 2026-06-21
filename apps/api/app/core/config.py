from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "YouTube Transcript Chatbot API"
    app_env: str = "local"
    web_origin: str = "http://localhost:3000"
    web_origins: str | None = None
    hf_token: str | None = None
    hf_model: str = "openai/gpt-oss-120b:fastest"
    hf_timeout_seconds: float = 20.0
    embedding_provider: str = "huggingface"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_timeout_seconds: float = 30.0
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 4

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_web_origins(self) -> list[str]:
        raw_origins = self.web_origins or self.web_origin
        return [
            origin.strip()
            for origin in raw_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
