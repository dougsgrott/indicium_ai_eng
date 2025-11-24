import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- API Keys ---
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str | None = None  # Optional, falls back to DDG if missing

    # --- Project Structure ---
    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = BASE_DIR / "data"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    
    # --- Data Paths ---
    DB_FILENAME: str = "INFLUD19-26-06-2025.db"
    
    @property
    def DB_PATH(self) -> Path:
        return self.DATA_DIR / self.DB_FILENAME

    @property
    def DB_URI(self) -> str:
        return f"sqlite:///{self.DB_PATH}"

    @property
    def IMG_OUTPUT_DIR(self) -> Path:
        return self.REPORTS_DIR / "images"

    @property
    def REPORT_OUTPUT_DIR(self) -> Path:
        return self.REPORTS_DIR / "generated"

    @property
    def TEMPLATE_DIR(self) -> Path:
        return self.REPORTS_DIR / "templates"

    # --- LangSmith Tracing ---
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_PROJECT: str = "sars-poc-agent"

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Singleton instance
settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(exist_ok=True)
settings.IMG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)