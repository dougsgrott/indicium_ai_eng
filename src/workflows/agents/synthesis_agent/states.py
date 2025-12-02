from typing import TypedDict, List, Dict, Any

class SynthesisAgentState(TypedDict):
    # Inputs (Context from upstream agents)
    # metrics: Dict[str, float]
    # news_snippets: List[Dict]
    # chart_data: Dict[str, Any]
    
    # Output (To be consumed by Report Maker)
    synthesis_result: Dict[str, str] # Structured analysis (e.g., {'summary': '...', 'risk': '...'})