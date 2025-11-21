# agent_schema.py

from typing import TypedDict, Sequence, Annotated, Dict, Any, List, Union
from langchain_core.messages import BaseMessage
from operator import add
from pydantic import BaseModel, Field

# --- A. GRAPH STATE ---

class AgentState(TypedDict):
    """
    Represents the state of the agent run in a structured, deterministic way.
    The 'messages' history is kept minimal to avoid passing large data to the LLM.
    """
    messages: Annotated[Sequence[BaseMessage], add]  # Standard message history (kept small)
    
    # Structured slots to hold large, processed data outside the main message history
    metrics_json: str  # Output from SQL/Mock Tool
    news_snippets: List[Dict[str, str]] # Output from Search/Mock Tool
    charts_html: Dict[str, str] # HTML content read from files
    
    # Final data structure that the synthesis step will create and the report tool consumes
    final_report_json_str: str

# --- B. PYDANTIC OUTPUT SCHEMA (For LLM Synthesis) ---

class ChartPaths(BaseModel):
    """Defines the structure for chart data in the final report JSON."""
    daily_30d_html: str = Field(description="The full HTML string content for the daily chart.")
    monthly_12m_html: str = Field(description="The full HTML string content for the monthly chart.")

class MetricsData(BaseModel):
    """Defines the metrics structure in the final report JSON."""
    mortality_rate: str
    rate_of_increase: str
    icu_occupancy: Union[str, int]
    vaccination_rate: str

class NewsSnippet(BaseModel):
    """The structure of a single news result entry."""
    title: str
    url: str
    content: str

class CommentaryData(BaseModel):
    """Defines the structure for synthesized text in the final report JSON."""
    # Ensure all fields are explicitly included but let Pydantic handle required status
    # Note: Using Pydantic V2 style to explicitly set descriptions, which is standard.
    summary: str = Field(description="A synthesized one-paragraph summary of the outbreak scenario.")
    news_sources: List[NewsSnippet] = Field(description="The exact list of structured news snippets used for synthesis.")

class FinalReportData(BaseModel):
    """
    The complete and definitive JSON structure required for the generate_final_report tool.
    The LLM MUST adhere to this schema when generating the final JSON string.
    """
    metrics: MetricsData = Field(...)
    charts: ChartPaths = Field(...)
    commentary: CommentaryData = Field(...)