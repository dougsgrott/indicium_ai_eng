# src/workflows/agents/metrics_analyst_llm/config.py

from pydantic import BaseModel, Field, SecretStr

# We define the schema context for the LLM so it knows how to query correctly.
DATA_DICTIONARY = """
You have access to a table named 'srag_records'.
Here are the critical columns and their value mappings:

1. DT_NOTIFIC (Date): The notification date of the case. Format: YYYY-MM-DD.
2. EVOLUCAO (Outcome):
   - 1: Cure / Discharge
   - 2: Death (Use this to calculate Mortality)
   - 3: Death from other causes
   - 9 or NULL: Ignored / Under Treatment (Exclude from denominator in mortality calc)
3. UTI (ICU Admission):
   - 1: Yes (Admitted to ICU)
   - 2: No
   - 9 or NULL: Ignored
4. VACINA (Vaccination Status):
   - 1: Yes (Vaccinated)
   - 2: No
   - 9 or NULL: Ignored
"""


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