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

# Define Shared State for the Pipeline
class ChartPipelineState(TypedDict):
    # Input
    raw_data: pd.DataFrame
    include_charts: bool
    
    # Intermediate (Produced by Calculator, Consumed by Designer)
    chart_data: Dict[str, Any] 
    
    # Output (Produced by Designer)
    charts_html: Dict[str, str]

class ChartPipelineWorkflow:
    name = "ChartPipeline"
    description = "End-to-End Chart Generation: Data Extraction -> Visualization"

    def __init__(self, config: MetricConfig):
        self.config = config
        
        # 1. Initialize Infrastructure
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
        self.design_node = ChartDesignerNode(self.llm) # Designer is deterministic

    def _construct_graph(self):
        workflow = StateGraph(ChartPipelineState)
        
        # Add Nodes
        workflow.add_node("calculator", self.calc_node.execute)
        workflow.add_node("designer", self.design_node.execute)
        
        # Define Flow
        # Data flows from Calculator (extracts numbers) to Designer (makes images)
        workflow.set_entry_point("calculator")
        workflow.add_edge("calculator", "designer")
        workflow.add_edge("designer", END)
        
        return workflow.compile()

    def run(self):
        print(f"[{self.name}] Pipeline Started.")
        
        # 1. Load Data
        try:
            print(f"[{self.name}] Loading raw data...")
            df = self.adapter.get_raw_srag_data()
        except Exception as e:
            print(f"[{self.name}] Critical Error Loading Data: {e}")
            return None

        # 2. Prepare Initial State
        initial_state = {
            "raw_data": df,
            "include_charts": True,
            "chart_data": {},
            "charts_html": {}
        }
        
        # 3. Execute Graph
        app = self._construct_graph()
        return app.invoke(initial_state)