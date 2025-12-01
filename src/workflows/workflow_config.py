# src/workflows/workflow_config.py

from pydantic import BaseModel, Field, SecretStr

class MetricConfig(BaseModel):
    """
    Configuration object for the Metric Analyst Workflow.
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

    class Config:
        arbitrary_types_allowed = True