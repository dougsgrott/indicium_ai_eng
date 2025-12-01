# src/workflows/metrics_workflow.py

from langgraph.graph import StateGraph
import pandas as pd
from .agents.news_researcher.node import NewsResearcherNode
from .agents.news_researcher.states import NewsState
from .base_workflow import BaseWorkflow

class NewsResearshertWorkflow(BaseWorkflow):
    name = "NewsResearsher"
    description = "Search online for news and articles regarding a topic."

    def __init__(self):
        self.state_schema = NewsState

    def _construct_graph(self):
        workflow = StateGraph(NewsState)
        # Nodes
        workflow.add_node("news_researcher", NewsResearcherNode().execute)
        # Flow
        workflow.set_entry_point("news_researcher")
        return workflow
