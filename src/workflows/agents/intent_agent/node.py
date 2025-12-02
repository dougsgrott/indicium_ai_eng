# src/workflows/agents/intent_agent/nodes.py

from src.nodes.base import BaseNode
from .prompts import INTENT_SYSTEM_PROMPT
import json


class IntentNode(BaseNode):

    def __init__(self, llm):
        super().__init__(llm, "IntentClassifier")

    def execute(self, state: dict) -> dict:
        user_prompt = state.get("user_prompt")
        print(f"[{self.name}] Analyzing request: '{user_prompt}'")

        # Fallback for empty prompt -> Full Report
        if not user_prompt:
            print("No user prompt provided. Creating full report.")
            return {"include_metrics": True, "include_charts": True, "include_news": True}

        response = self._invoke_llm(INTENT_SYSTEM_PROMPT, user_prompt)

        try:
            # Simple cleanup to ensure JSON parsing
            clean_json = response.replace("```json", "").replace("```", "").strip()
            flags = json.loads(clean_json)

            if "is_off_topic" not in flags:
                flags["is_off_topic"] = False

            print(f"[{self.name}] Routing Decision: {flags}")
            return flags
        except Exception as e:
            print(f"[{self.name}] Parsing Error: {e}. Defaulting to FULL report.")
            return {
                "include_metrics": True,
                "include_charts": True,
                "include_news": True,
                "is_off_topic": False
            }