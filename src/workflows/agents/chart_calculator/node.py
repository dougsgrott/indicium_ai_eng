import json
import re
import pandas as pd
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent

from src.nodes.base import BaseNode
from .prompts import (
    SYSTEM_PROMPT, 
    CHART_CALCULATION_PROMPT, 
    REQUEST_CHARTS, 
    REFERENCE_DATE_CONTEXT,
)
from src.domain.srag.schema_context import DATA_DICTIONARY_TEXT

class ChartCalculatorNode(BaseNode):
    def __init__(self, llm):
        super().__init__(llm, "ChartCalculator")

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
            print(f"[{self.name}] Failed to parse JSON. Raw: {raw_output[:100]}...")
            return {}

    def _normalize_sql_result(self, data_list):
        """
        Helper to normalize keys (date/count) from loose SQL output.
        """
        if not data_list: return []
        
        normalized = []
        for item in data_list:
            # Find the date value
            date_val = item.get('date') or item.get('DT_NOTIFIC') or item.get('dt_notific')
            # Find the count value (or fallback to any int)
            count_val = item.get('count') or item.get('total') or item.get('cases')
            
            # If count missing, try to find first numeric value
            if count_val is None:
                for v in item.values():
                    if isinstance(v, (int, float)):
                        count_val = v
                        break
            
            if date_val:
                normalized.append({
                    'date': date_val, 
                    'count': int(count_val) if count_val else 0
                })
        return normalized

    def _fill_daily_gaps(self, sparse_data: list, end_date: pd.Timestamp) -> list:
        # 1. Normalize Input Keys
        clean_data = self._normalize_sql_result(sparse_data)
        
        # 2. Build Target Date Range (Strings)
        # We use strings for reliable dictionary lookups
        idx = pd.date_range(end=end_date, periods=30, freq='D')
        date_map = {d.strftime('%Y-%m-%d'): 0 for d in idx}
        
        # 3. Map SQL Results to Date Range
        for item in clean_data:
            d_str = str(item['date'])[:10] # Ensure YYYY-MM-DD
            if d_str in date_map:
                date_map[d_str] = item['count']
                
        # 4. Convert back to List[Dict] sorted by date
        return [{"date": d, "count": c} for d, c in date_map.items()]

    def _fill_monthly_gaps(self, sparse_data: list, end_date: pd.Timestamp) -> list:
        clean_data = self._normalize_sql_result(sparse_data)
        
        # Target: Last 12 months, anchored to start of month
        start_date = end_date - pd.DateOffset(months=11)
        idx = pd.date_range(start=start_date, periods=12, freq='MS')
        date_map = {d.strftime('%Y-%m'): 0 for d in idx}
        
        for item in clean_data:
            # Handle various date formats (2023-01-01 or 2023-01)
            d_str = str(item['date'])[:7] # YYYY-MM
            if d_str in date_map:
                date_map[d_str] += item['count'] # Sum if multiple entries per month
        
        return [{"date": d, "count": c} for d, c in date_map.items()]

    def execute(self, state: dict) -> dict:
        df = state.get('raw_data', pd.DataFrame())
        if df.empty: return {"chart_data": {}}

        # Check if charts are requested
        if not state.get("include_charts", True):
            return {"chart_data": {}}

        # Date Prep
        df_analysis = df.copy()
        df_analysis['DT_NOTIFIC'] = pd.to_datetime(df_analysis['DT_NOTIFIC'], errors='coerce')
        
        try:
            latest_date = df_analysis['DT_NOTIFIC'].max()
            if pd.isna(latest_date): raise ValueError("No dates")
            
            ref_context = REFERENCE_DATE_CONTEXT.format(
                reference_date=latest_date.strftime('%Y-%m-%d'),
                date_30d_ago=(latest_date - pd.Timedelta(days=30)).strftime('%Y-%m-%d'),
                date_12m_ago=(latest_date - pd.DateOffset(months=12)).strftime('%Y-%m-%d')
            )
        except Exception:
            latest_date = pd.Timestamp.now()
            ref_context = ""

        # SQL Agent Setup
        db = self._create_ephemeral_db(df)
        agent_executor = create_sql_agent(
            llm=self.llm, db=db, agent_type="openai-tools", verbose=False
        )

        try:
            print(f"[{self.name}] Calculating Chart Data...")
            prompt = CHART_CALCULATION_PROMPT.format(
                data_dictionary=DATA_DICTIONARY_TEXT,
                reference_context=ref_context,
                request=REQUEST_CHARTS
            )
            
            response = agent_executor.invoke({"input": prompt, "system_message": SYSTEM_PROMPT})
            data = self._parse_response(response["output"])
            
            # Post-Processing with robust gap filling
            processed_data = {
                "daily_cases_30d": self._fill_daily_gaps(data.get('daily_cases_30d', []), latest_date),
                "monthly_cases_12m": self._fill_monthly_gaps(data.get('monthly_cases_12m', []), latest_date)
            }
            
            print(f"[{self.name}] Charts Data Ready.")
            return {"chart_data": processed_data}

        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            return {"chart_data": {"error": str(e)}}