# src/workflows/agents/metrics_analyst/node.py

import pandas as pd
from src.nodes.base import BaseNode
from .config import *

class MetricsAnalystNode(BaseNode):
    def __init__(self, llm):
        super().__init__(llm, "MetricsAnalyst")

    def execute(self, state: dict) -> dict:
        df = state['raw_data']
        
        # Ensure date format
        df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors='coerce')
        
        # 1. Mortality Rate (Deaths / Total Outcomes Known)
        # We filter for rows where the case is closed (Evolution is known)
        closed_cases = df[df[COL_EVOLUTION].notna()]
        deaths = closed_cases[closed_cases[COL_EVOLUTION] == VAL_DEATH]
        mortality_rate = (len(deaths) / len(closed_cases)) * 100 if not closed_cases.empty else 0.0

        # 2. ICU Occupancy Rate (ICU Yes / Total Reported ICU Status)
        # Assuming the dataset represents all hospitalized, this metric represents 
        # severity: % of hospitalized needing ICU.
        valid_icu = df[df[COL_ICU].isin([1, 2])] # Filter out ignored/null
        icu_patients = valid_icu[valid_icu[COL_ICU] == VAL_ICU_YES]
        icu_rate = (len(icu_patients) / len(valid_icu)) * 100 if not valid_icu.empty else 0.0

        # 3. Vaccination Rate (Vaccinated / Total Cases)
        valid_vac = df[df[COL_VACCINE].isin([1, 2])]
        vaccinated = valid_vac[valid_vac[COL_VACCINE] == VAL_VAC_YES]
        vac_rate = (len(vaccinated) / len(valid_vac)) * 100 if not valid_vac.empty else 0.0

        # 4. Rate of Case Increase (Last 30 days vs Previous 30 days)
        # This is a simplifed calculation for the PoC
        latest_date = df[COL_DATE].max()
        cutoff_30 = latest_date - pd.Timedelta(days=30)
        cutoff_60 = latest_date - pd.Timedelta(days=60)

        cases_last_30 = df[(df[COL_DATE] > cutoff_30) & (df[COL_DATE] <= latest_date)]
        cases_prev_30 = df[(df[COL_DATE] > cutoff_60) & (df[COL_DATE] <= cutoff_30)]

        count_current = len(cases_last_30)
        count_prev = len(cases_prev_30)
        
        if count_prev > 0:
            increase_rate = ((count_current - count_prev) / count_prev) * 100
        else:
            increase_rate = 0.0

        metrics = {
            "mortality_rate": round(mortality_rate, 2),
            "icu_rate": round(icu_rate, 2),
            "vaccination_rate": round(vac_rate, 2),
            "increase_rate": round(increase_rate, 2),
            "total_cases_analyzed": len(df)
        }

        print(f"[{self.name}] Computed Metrics: {metrics}")
        return {"metrics": metrics}