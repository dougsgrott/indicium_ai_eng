import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- API Keys ---
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str | None = None
    
    # --- LangSmith Tracing ---
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_PROJECT: str = "sars-poc-agent"

    # --- Langfuse Tracing (Self-Hosted) ---
    LANGFUSE_ENABLED: bool = False
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_HOST: str = "http://localhost:3000"
    
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

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Singleton instance
settings = Settings()

# --- Export Environment Variables ---

# 1. LangSmith Export
if settings.LANGCHAIN_TRACING_V2.lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    if settings.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY

# 2. NEW: Langfuse Export
# While we pass the handler explicitly, setting these ensures 
# that internal LangChain components can find them if needed.
if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST

# Ensure directories exist
settings.DATA_DIR.mkdir(exist_ok=True)
settings.IMG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)