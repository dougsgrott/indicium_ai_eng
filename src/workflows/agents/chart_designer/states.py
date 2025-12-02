# src/workflows/agents/chart_designer/states.py
from typing import TypedDict, Dict, Any

class ChartDesignerState(TypedDict):
    charts_html: Dict[str, str]