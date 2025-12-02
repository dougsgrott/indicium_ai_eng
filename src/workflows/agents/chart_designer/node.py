import uuid
import json
from src.nodes.base import BaseNode
from .prompts import SYSTEM_PROMPT, CHART_GENERATION_PROMPT

class ChartDesignerNode(BaseNode):
    def __init__(self, llm):
        # LLM is now REQUIRED
        if llm is None:
            raise ValueError("ChartDesignerNode now requires an LLM instance.")
        super().__init__(llm, "ChartDesigner")

    def _generate_chart_snippet(self, data: list, title: str, chart_type: str, color: str) -> str:
        if not data:
            return f"<div style='padding:20px; text-align:center'>Sem dados para: {title}</div>"

        # 1. Generate Unique ID to prevent overlap collisions
        unique_id = f"chart_{uuid.uuid4().hex}"

        # 2. Prepare Prompt
        # We dump the data to JSON string for the LLM to read
        data_json = json.dumps(data, indent=2)
        
        user_prompt = CHART_GENERATION_PROMPT.format(
            title=title,
            chart_type=chart_type,
            div_id=unique_id,
            color=color,
            data_json=data_json
        )

        # 3. Invoke LLM
        try:
            print(f"[{self.name}] Asking LLM to generate {chart_type} chart for '{title}'...")
            response = self._invoke_llm(SYSTEM_PROMPT, user_prompt)
            
            # 4. Clean Output (Strip Markdown if present)
            clean_html = response.replace("```html", "").replace("```", "").strip()
            
            return clean_html

        except Exception as e:
            print(f"[{self.name}] Error generating chart: {e}")
            return f"<!-- Error generating chart: {e} -->"

    def execute(self, state: dict) -> dict:
        chart_data = state['chart_calc_state'].get("chart_data", {})
        key_str = "chart_plot_state"
        output = {key_str: {}}
        charts_html = {}
        
        print(f"[{self.name}] Generating Visualizations via LLM...")

        # 1. Daily Chart (Bar)
        charts_html["daily_30d_html"] = self._generate_chart_snippet(
            data=chart_data.get("daily_cases_30d", []),
            title="Casos Diários (Últimos 30 Dias)",
            chart_type="bar",
            color="#2E86C1"
        )

        # 2. Monthly Chart (Line)
        charts_html["monthly_12m_html"] = self._generate_chart_snippet(
            data=chart_data.get("monthly_cases_12m", []),
            title="Evolução Mensal (Últimos 12 Meses)",
            chart_type="line",
            color="#C0392B"
        )

        print(f"[{self.name}] Charts Generated.")
        output[key_str]["charts_html"] = charts_html
        return output
        # return {key_str: {"charts_html": charts_html}}
        # return {"charts_html": charts_html}