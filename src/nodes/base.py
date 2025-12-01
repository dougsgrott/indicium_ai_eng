# sars_lens/nodes/base.py
from langchain_core.messages import HumanMessage, SystemMessage

class BaseNode:
    def __init__(self, llm, name: str):
        self.llm = llm
        self.name = name

    def _invoke_llm(self, system_prompt: str, user_content: str) -> str:
        """
        Standard wrapper for LLM calls with error handling.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ]
        response = self.llm.invoke(messages)
        return response.content

    def execute(self, state: dict):
        """
        Abstract method to be implemented by child nodes.
        """
        raise NotImplementedError