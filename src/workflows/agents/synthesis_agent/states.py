from typing import TypedDict, List, Dict, Any

class SynthesisState(TypedDict):
    # Inputs (Context from upstream agents)
    metrics: Dict[str, float]       # From Metrics Analyst
    news_snippets: List[Dict]       # From News Researcher
    chart_data: Dict[str, Any]      # From Chart Calculator (Raw time-series)
    
    # Output (To be consumed by Report Maker)
    synthesis_result: Dict[str, str] # Structured analysis (e.g., {'summary': '...', 'risk': '...'})