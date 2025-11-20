from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Matches OPENAI_API_KEY in .env (case-insensitive by default)
    OPENAI_API_KEY: Optional[str] = None

    TAVILY_API_KEY: Optional[str] = None

    # --- LangSmith Configuration ---
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "Finance_RAG_Agent_v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()