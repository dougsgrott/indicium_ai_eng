from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from .agents.synthesis_agent.node import SynthesisNode
from .agents.synthesis_agent.states import SynthesisState
from .workflow_config import MetricConfig

class SynthesisWorkflow:
    name = "SynthesisWorkflow"
    description = "Generates structured epidemiological insights from raw data"

    def __init__(self, config: MetricConfig):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.llm_model, 
            temperature=0.2, # Slightly higher temp for creative analysis
            api_key=config.openai_api_key.get_secret_value()
        )
        self.node = SynthesisNode(self.llm)

    def _construct_graph(self):
        workflow = StateGraph(SynthesisState)
        workflow.add_node("synthesizer", self.node.execute)
        workflow.set_entry_point("synthesizer")
        workflow.add_edge("synthesizer", END)
        return workflow.compile()

    def run(self, state: dict):
        app = self._construct_graph()
        return app.invoke(state)