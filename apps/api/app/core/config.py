from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "YouTube Transcript Chatbot API"
    app_env: str = "local"
    web_origin: str = "http://localhost:3000"
    hf_token: str | None = None
    hf_model: str = "openai/gpt-oss-120b:fastest"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()

