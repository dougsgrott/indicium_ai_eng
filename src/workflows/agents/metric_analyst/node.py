import json
import re
import pandas as pd
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent

from src.nodes.base import BaseNode 
from src.domain.sars.schema_context import DATA_DICTIONARY_TEXT

from .prompts import (
    SYSTEM_PROMPT, 
    METRICS_CALCULATION_PROMPT, 
    REQUEST_METRICS, 
    REFERENCE_DATE_CONTEXT
)

class MetricsAnalystNode(BaseNode):
    def __init__(self, llm):
        super().__init__(llm, "MetricsAnalyst")

    def _create_ephemeral_db(self, df: pd.DataFrame) -> SQLDatabase:
        engine = create_engine("sqlite:///:memory:")
        df.to_sql("srag_records", engine, index=False, if_exists='replace')
        return SQLDatabase(engine=engine)

    def _parse_response(self, raw_output: str) -> dict:
        try:
            match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(raw_output)
        except json.JSONDecodeError:
            print(f"[{self.name}] Failed to parse JSON: {raw_output[:50]}...")
            return {}

    def _sanitize_metrics(self, metrics: dict) -> dict:
        """
        Post-processing to ensure data quality for the report.
        Handles None values and scaling issues (0.12 vs 12.0).
        """
        cleaned = {}
        # Metrics that are definitely 0-100 percentages
        percentage_keys = ["mortality_rate", "icu_rate", "vaccination_rate"]
        
        for k, v in metrics.items():
            if v is None:
                cleaned[k] = 0.0
                continue
                
            if isinstance(v, (int, float)):
                # Heuristic: If a known percentage metric is <= 1.0, 
                # the LLM likely returned a ratio (0.12) instead of % (12.0).
                # We fix it here.
                if k in percentage_keys and abs(v) <= 1.0 and v != 0:
                    cleaned[k] = round(v * 100, 2)
                else:
                    cleaned[k] = round(v, 2)
            else:
                cleaned[k] = v
                
        return cleaned

    def execute(self, state: dict) -> dict:
        key_str = "metrics_state"
        output = {key_str: {}}

        # --- SAFEGUARD: SHORT CIRCUIT ---
        if state.get("is_off_topic", False):
            print(f"[{self.name}] 🛡️ Safeguard triggered: Off-topic prompt. Skipping SQL.")
            # Return empty metrics structure so ReportMaker doesn't crash
            output[key_str] = {"metrics": {}} 
            return output

        df = state.get('raw_data', pd.DataFrame())
        if df.empty:
            print(f"[{self.name}] Warning: DataFrame is empty.")
            return output

        # Ensure DT_NOTIFIC is datetime
        df_analysis = df.copy()
        df_analysis['DT_NOTIFIC'] = pd.to_datetime(df_analysis['DT_NOTIFIC'], errors='coerce')
        
        # 1. Determine Time Anchor
        try:
            latest_date = df_analysis['DT_NOTIFIC'].max()
            if pd.isna(latest_date):
                raise ValueError("No valid dates found")
            
            date_30d_ago = latest_date - pd.Timedelta(days=30)
            
            ref_context = REFERENCE_DATE_CONTEXT.format(
                reference_date=latest_date.strftime('%Y-%m-%d'),
                date_30d_ago=date_30d_ago.strftime('%Y-%m-%d')
            )
        except Exception as e:
            print(f"[{self.name}] Date calculation warning: {e}. using defaults.")
            latest_date = pd.Timestamp.now()
            ref_context = ""

        # 2. Build Request
        if not state.get("include_metrics", True):
            print(f"[{self.name}] Skipped (Metrics disabled).")
            return output

        # 3. Setup & Execute Agent
        db = self._create_ephemeral_db(df) 
        agent_executor = create_sql_agent(
            llm=self.llm,
            db=db,
            agent_type="openai-tools",
            verbose=False 
        )

        try:
            print(f"[{self.name}] Executing SQL Agent...")
            
            user_prompt = METRICS_CALCULATION_PROMPT.format(
                data_dictionary=DATA_DICTIONARY_TEXT,
                reference_context=ref_context,
                request=REQUEST_METRICS
            )
            
            response = agent_executor.invoke({
                "input": user_prompt, 
                "system_message": SYSTEM_PROMPT
            })
            
            raw_metrics = self._parse_response(response["output"])
            
            # 4. Sanitize Results
            metrics = self._sanitize_metrics(raw_metrics)
            metrics["total_cases_analyzed"] = len(df)

            print(f"[{self.name}] Metrics Calculated: {metrics}")
            output[key_str] = metrics
            return output

        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            output[key_str] = {"error": str(e)}
            return output