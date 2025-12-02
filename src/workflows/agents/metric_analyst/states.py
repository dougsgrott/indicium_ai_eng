# src/workflows/agents/metric_analyst_llm/states.py

from typing import TypedDict
import pandas as pd

class MetricState(TypedDict):
    raw_data: pd.DataFrame
    metrics: dict
