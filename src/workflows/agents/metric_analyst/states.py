# src/workflows/agents/metric_analyst_llm/states.py

from typing import TypedDict
import pandas as pd

class Metrics(TypedDict):
    metrics: dict
