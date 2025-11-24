from typing import TypedDict, Sequence, Annotated, Dict, List, Union
from langchain_core.messages import BaseMessage
from operator import add
from pydantic import BaseModel, Field

# --- GRAPH STATE ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add]
    metrics_json: str
    news_snippets: List[Dict[str, str]]
    charts_html: Dict[str, str]
    final_report_json_str: str

# --- OUTPUT SCHEMA ---
class ChartPaths(BaseModel):
    daily_30d_html: str = Field(description="HTML content for the daily chart.")
    monthly_12m_html: str = Field(description="HTML content for the monthly chart.")

class MetricsData(BaseModel):
    mortality_rate: str
    rate_of_increase: str
    icu_occupancy: Union[str, int]
    vaccination_rate: str

class NewsSnippet(BaseModel):
    title: str
    url: str
    content: str

class CommentaryData(BaseModel):
    summary: str = Field(description="Synthesized summary of the outbreak.")
    news_sources: List[NewsSnippet] = Field(description="List of news used.")

class FinalReportData(BaseModel):
    metrics: MetricsData
    charts: ChartPaths
    commentary: CommentaryData