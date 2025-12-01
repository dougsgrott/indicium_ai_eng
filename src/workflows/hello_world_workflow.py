# src/workflows/srag_workflow.py

from langgraph.graph import StateGraph
import pandas as pd
from .agents.greeter.node import GreeterNode
from .agents.greeter.states import GreeterState
from .base_workflow import BaseWorkflow

class GreeterWorkflow(BaseWorkflow):
    name = "Greeter"
    description = "Generate a greeting with the user_name"

    def __init__(self):
        self.state_schema = GreeterState

    def _construct_graph(self):
        workflow = StateGraph(GreeterState)
        # Nodes
        workflow.add_node("greeter", GreeterNode().execute)
        # Flow
        workflow.set_entry_point("greeter")
        return workflow
