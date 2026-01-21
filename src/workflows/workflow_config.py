# src/workflows/workflow_config.py

from pydantic import BaseModel, Field, SecretStr
from typing import Optional

class Config(BaseModel):
    """
    Centralizes all environment and path settings required for execution.
    """
    # LLM Settings
    openai_api_key: SecretStr = Field(..., description="API Key for OpenAI")
    llm_model: str = Field(default="gpt-4o", description="Model name to use")
    temperature: float = Field(default=0.0, description="LLM Temperature")

    # Data Settings
    db_uri: str = Field(..., description="URI for the SQLite database (e.g. sqlite:///path/to/db)")
    
    # Project Paths (for resolving relative DB paths)
    project_root: str = Field(..., description="Absolute path to project root")

    langfuse_enabled: bool = Field(default=False)
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "http://localhost:3000"

    class Config:
        arbitrary_types_allowed = True