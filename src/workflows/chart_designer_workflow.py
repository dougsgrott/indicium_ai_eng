from typing import TypedDict, Dict, Any
import pandas as pd
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# Import Nodes
from .agents.chart_calculator.node import ChartCalculatorNode
from .agents.chart_designer.node import ChartDesignerNode

# Import Infrastructure
from internal.data_retrieval.adapters.sqlite_loader import SqliteSragAdapter
from .workflow_config import MetricConfig

class ChartPipelineState(TypedDict):
    raw_data: pd.DataFrame
    include_charts: bool
    chart_data: Dict[str, Any] 
    charts_html: Dict[str, str]

class ChartPipelineWorkflow:
    name = "ChartPipeline"
    description = "End-to-End Chart Generation"

    def __init__(self, config: MetricConfig):
        self.config = config
        
        self.llm = ChatOpenAI(
            model=config.llm_model, 
            temperature=config.temperature,
            api_key=config.openai_api_key.get_secret_value()
        )
        
        self.adapter = SqliteSragAdapter(
            db_uri=config.db_uri, 
            root_dir=config.project_root
        )
        
        # 2. Initialize Nodes
        self.calc_node = ChartCalculatorNode(self.llm)
        
        # FIX: Pass self.llm instead of None
        self.design_node = ChartDesignerNode(self.llm) 

    def _construct_graph(self):
        workflow = StateGraph(ChartPipelineState)
        workflow.add_node("calculator", self.calc_node.execute)
        workflow.add_node("designer", self.design_node.execute)
        
        workflow.set_entry_point("calculator")
        workflow.add_edge("calculator", "designer")
        workflow.add_edge("designer", END)
        
        return workflow.compile()

    def run(self):
        print(f"[{self.name}] Pipeline Started.")
        try:
            print(f"[{self.name}] Loading raw data...")
            df = self.adapter.get_raw_srag_data()
        except Exception as e:
            print(f"[{self.name}] Critical Error Loading Data: {e}")
            return None

        initial_state = {
            "raw_data": df,
            "include_charts": True,
            "chart_data": {},
            "charts_html": {}
        }
        
        app = self._construct_graph()
        return app.invoke(initial_state)