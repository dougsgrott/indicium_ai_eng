import json
from src.nodes.base import BaseNode

class ReportMakerNode(BaseNode):
    def __init__(self, report_tool):
        # This node is deterministic; it uses the report_tool, not an LLM directly.
        super().__init__(llm=None, name="ReportMaker")
        self.report_tool = report_tool

    def _format_commentary(self, synthesis: dict) -> str:
        """
        Combines the structured synthesis insights into a single HTML/Markdown block 
        suitable for the report's 'Summary' section.
        """
        if not synthesis:
            return "No analysis provided."

        # We construct a formatted string that preserves the structure
        # inferred from the Synthesis Agent's output keys.
        parts = []
        
        if "executive_summary" in synthesis:
            parts.append(f"<h3>Executive Summary</h3><p>{synthesis['executive_summary']}</p>")
            
        if "risk_assessment" in synthesis:
            # Color-code risk if possible (simple heuristic)
            risk = synthesis['risk_assessment']
            color = "red" if "High" in risk or "Critical" in risk else "black"
            parts.append(f"<h3>Risk Assessment</h3><p style='color:{color}; font-weight:bold'>{risk}</p>")
            
        if "deep_dive" in synthesis:
            parts.append(f"<h3>Contextual Deep Dive</h3><p>{synthesis['deep_dive']}</p>")
            
        return "".join(parts)

    def execute(self, state: dict) -> dict:
        print(f"[{self.name}] Assembling Report Data...")
        
        # 1. Retrieve Data
        metrics = state.get("metrics_state", {})
        charts = state['chart_plot_state'].get("charts_html", {})
        news = state.get("news_state", {}).get("news_snippets", [])
        synthesis = state.get("synthesis_state", {}).get("synthesis_result", {})

        # 2. Adapt Synthesis to Report Schema
        # The Jinja template expects 'commentary.summary' and 'commentary.news_sources'
        formatted_summary = self._format_commentary(synthesis)
        
        # 3. Construct Payload for Tool
        report_payload = {
            "metrics": metrics,
            "charts": charts,
            "commentary": {
                "summary": formatted_summary,
                "news_sources": news
            }
        }

        # 4. Invoke Tool
        try:
            # The tool expects a JSON string
            payload_json = json.dumps(report_payload)
            result_msg = self.report_tool.invoke(payload_json)
            
            # Extract path from success message if possible, or just return message
            # Format: "Success: Report saved to /path/to/file.html"
            final_path = result_msg.replace("Report successfully saved to: ", "").strip()
            
            print(f"[{self.name}] Report Generated.")
            return {"final_report_path": final_path}

        except Exception as e:
            print(f"[{self.name}] Error assembling report: {e}")
            return {"final_report_path": f"Error: {e}"}