# src/workflows/agent_state.py

from typing import TypedDict, List, Any, Dict
import pandas as pd

class AgentState(TypedDict):
    # Context
    raw_data: Any  # pd.DataFrame (Using Any to avoid Pydantic validation issues with DataFrames)
    
    # Outputs from Agents
    metrics: Dict[str, float]       # From Metrics Analyst
    news_analysis: str              # From News Researcher
    charts: List[str]               # From Chart Designer (Base64 strings)
    
    # Final Output
    final_report: str               # From Report Writer