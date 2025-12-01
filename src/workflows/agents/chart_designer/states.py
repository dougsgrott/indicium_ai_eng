from typing import TypedDict, Dict, Any

class ChartDesignerState(TypedDict):
    # Input: Raw data from Chart Calculator
    # Structure: {'daily_cases_30d': [{'date':..., 'count':...}], 'monthly_cases_12m': [...]}
    chart_data: Dict[str, Any]
    
    # Output: HTML strings for embedding
    charts_html: Dict[str, str]