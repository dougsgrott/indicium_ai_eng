import json
import re
from src.nodes.base import BaseNode
from .prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT

class SynthesisNode(BaseNode):
    def __init__(self, llm):
        super().__init__(llm, "SynthesisAgent")

    def _format_metrics(self, metrics: dict) -> str:
        if not metrics: return "No metrics available."
        return "\n".join([f"- {k}: {v}" for k, v in metrics.items()])

    def _format_news(self, news: list) -> str:
        if not news: return "No news available."
        return "\n".join([f"- {n.get('title', '')}: {n.get('content', '')[:150]}..." for n in news])

    def _format_chart_summary(self, chart_data: dict) -> str:
        # Provide the LLM with a text summary of the visual data so it can analyze the trend
        daily = chart_data['chart_data'].get('daily_cases_30d', [])
        if not daily: return "No trend data."
        
        start = daily[0]['count']
        end = daily[-1]['count']
        peak = max([d['count'] for d in daily])
        return f"Daily Cases (30d): Started at {start}, Peaked at {peak}, Ended at {end}."

    def execute(self, state: dict) -> dict:
        output = {"synthesis_state": {}}

        # --- SAFEGUARD: SHORT CIRCUIT ---
        if state.get("is_off_topic", False):
            print(f"[{self.name}] 🛡️ Safeguard triggered: Off-topic. Returning dummy synthesis.")
            output["synthesis_state"] = {
                "synthesis_result": {
                    "executive_summary": "Analysis skipped due to off-topic request.",
                    "risk_assessment": "N/A",
                    "deep_dive": "N/A"
                }
            }
            return output

        print(f"[{self.name}] Synthesizing Insights...")

        # 1. Prepare Inputs
        metrics_str = self._format_metrics(state.get('metrics_state', {}))
        news_str = self._format_news(state.get('news_snippets', []))
        chart_str = self._format_chart_summary(state.get('chart_calc_state', {}))

        # 2. Build Prompt
        user_prompt = ANALYSIS_PROMPT.format(
            metrics_section=metrics_str,
            news_section=news_str,
            chart_section=chart_str
        )

        # 3. Invoke LLM
        try:
            raw_response = self._invoke_llm(SYSTEM_PROMPT, user_prompt)
            
            # 4. Parse JSON Output
            # We use regex to find the JSON block in case the LLM adds chatter
            match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if match:
                synthesis_result = json.loads(match.group(0))
            else:
                # Fallback: Treat whole response as the 'deep_dive'
                synthesis_result = {
                    "executive_summary": "Auto-generated summary unavailable.",
                    "deep_dive": raw_response,
                    "risk_assessment": "Unknown"
                }
            output["synthesis_state"] = {"synthesis_result": synthesis_result}
            print(f"[{self.name}] Analysis Complete.")
            return output

        except Exception as e:
            print(f"[{self.name}] Error: {e}")
            output["synthesis_state"] = {
                "synthesis_result": {
                    "executive_summary": "Error during synthesis.",
                    "deep_dive": str(e),
                    "risk_assessment": "Error"
                }
            }
            return output