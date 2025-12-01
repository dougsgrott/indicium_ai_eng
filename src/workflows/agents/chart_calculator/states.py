from typing import TypedDict
import pandas as pd

class ChartState(TypedDict):
    # Input
    raw_data: pd.DataFrame
    include_charts: bool  # Control flag
    
    # Output
    chart_data: dict      # The calculated time-series data
