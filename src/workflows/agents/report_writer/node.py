from src.nodes.base import BaseNode
from .prompts import WRITER_SYSTEM_PROMPT, WRITER_USER_PROMPT

class ReportWriterNode(BaseNode):
    def __init__(self, llm):
        super().__init__(llm, "ReportWriter")

    def execute(self, state: dict) -> dict:
        metrics = state['metrics']
        news = state['news_analysis']
        
        # Prepare Prompt
        prompt = WRITER_USER_PROMPT.format(
            increase_rate=metrics.get('increase_rate'),
            mortality_rate=metrics.get('mortality_rate'),
            icu_rate=metrics.get('icu_rate'),
            vac_rate=metrics.get('vaccination_rate'),
            news_analysis=news
        )
        
        # Generate Text
        report_text = self._invoke_llm(WRITER_SYSTEM_PROMPT, prompt)
        
        # Append image logic (Simulated markdown embedding)
        # In a real app, you might upload base64 to S3 and link, or render HTML.
        # Here we just append a note about the attachments.
        final_report = report_text + "\n\n**[System Note]: 2 Charts have been generated and attached to this response.**"
        
        print(f"[{self.name}] Final Report Generated")
        return {"final_report": final_report}