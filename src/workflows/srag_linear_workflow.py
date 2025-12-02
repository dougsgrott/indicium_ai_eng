# src/workflows/srag_linear_workflow.py

import os
from typing import TypedDict, Dict, Any, List, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import operator

# 1. Import Configuration & Infrastructure
from .workflow_config import Config
from internal.data_retrieval.adapters.sqlite_loader import SqliteSragAdapter
from tools.report_tool import setup_report_tool

# 2. Import All Specialized Agent Nodes
from .agents.intent_agent.node import IntentNode
from .agents.metric_analyst.node import MetricsAnalystNode
from .agents.chart_calculator.node import ChartCalculatorNode
from .agents.chart_designer.node import ChartDesignerNode
from .agents.news_researcher.node import NewsResearcherNode
from .agents.synthesis_agent.node import SynthesisNode
from .agents.report_maker.node import ReportMakerNode

from .workflow_states import SragWorkflowState


class SragWorkflow:
    name = "SragOrchestrator"
    description = "End-to-End SARS Report Generation Pipeline"

    def __init__(self, config: Config):
        self.config = config
        
        # --- A. Initialize Shared Infrastructure ---
        self.llm = ChatOpenAI(
            model=config.llm_model, 
            temperature=0, 
            api_key=config.openai_api_key.get_secret_value()
        )
        
        self.adapter = SqliteSragAdapter(
            db_uri=config.db_uri, 
            root_dir=config.project_root
        )
        
        # Initialize Tool for Report Maker
        template_dir = os.path.join(config.project_root, "reports", "templates")
        output_dir = os.path.join(config.project_root, "reports", "generated")
        self.report_tool = setup_report_tool(template_dir, output_dir)

        # --- B. Initialize All Nodes ---
        # self.intent_node = IntentNode(self.llm)
        self.metrics_node = MetricsAnalystNode(self.llm)
        self.calc_node = ChartCalculatorNode(self.llm)
        self.design_node = ChartDesignerNode(self.llm)
        self.news_node = NewsResearcherNode(self.llm)
        self.synth_node = SynthesisNode(self.llm)
        self.maker_node = ReportMakerNode(self.report_tool)

    def _construct_graph(self):
        workflow = StateGraph(SragWorkflowState)
        
        # --- Add Nodes ---
        workflow.add_node("metrics_analyst", self.metrics_node.execute)
        workflow.add_node("chart_calculator", self.calc_node.execute)
        workflow.add_node("chart_designer", self.design_node.execute)
        workflow.add_node("news_researcher", self.news_node.execute)
        workflow.add_node("synthesis_agent", self.synth_node.execute)
        workflow.add_node("report_maker", self.maker_node.execute)

        # --- Define Flow (Linear Sequence for Stability) ---
        workflow.set_entry_point("metrics_analyst")
        workflow.add_edge("metrics_analyst", "chart_calculator") 
        workflow.add_edge("chart_calculator", "chart_designer") 
        workflow.add_edge("chart_designer", "news_researcher")
        workflow.add_edge("news_researcher", "synthesis_agent")
        workflow.add_edge("synthesis_agent", "report_maker")
        workflow.add_edge("report_maker", END)
        return workflow.compile()

    def load_data(self):
        """Helper to fetch data using the adapter before starting the graph."""
        print(f"[{self.name}] Loading Clinical Data...")
        try:
            return self.adapter.get_raw_srag_data()
        except Exception as e:
            print(f"[{self.name}] Data Load Error: {e}")
            raise e

    def run(self):
        """Main execution method."""
        # 1. Prepare Data
        df = self.load_data()
        
        # 2. Define Initial State
        initial_state = {
            "raw_data": df,
            "include_metrics": True,
            "include_charts": True,
            "include_news": True,
            # Initialize empty containers for safety
            "metrics": {},
            "chart_data": {},
            "charts_html": {},
            "news_snippets": [],
            "synthesis_result": {},
            "branches_completed": []
        }
        
        # 3. Execute Graph
        print(f"[{self.name}] Starting Workflow Graph...")
        app = self._construct_graph()
        result = app.invoke(initial_state)
        
        return result
