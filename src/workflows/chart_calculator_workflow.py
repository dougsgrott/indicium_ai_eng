# src/workflows/chart_calculator_workflow.py

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# Import Domain Components
from .agents.chart_calculator.node import MetricsAnalystNode
from .agents.chart_calculator.states import MetricState
# Assuming BaseWorkflow is an abstract class you have defined elsewhere
# from .base_workflow import BaseWorkflow 

# Import Adapter
from internal.data_retrieval.adapters.sqlite_loader import SqliteSragAdapter
from .workflow_config import MetricConfig

class MetricAnalystWorkflow:
    name = "MetricAnalyst"
    description = "Calculate metrics using prompts from the user"

    def __init__(self, config: MetricConfig):
        self.config = config
        self.state_schema = MetricState
        
        # 1. Initialize Infrastructure based on Config
        self.llm = ChatOpenAI(
            model=config.llm_model, 
            temperature=config.temperature,
            api_key=config.openai_api_key.get_secret_value()
        )
        
        # 2. Initialize Data Adapter based on Config
        self.adapter = SqliteSragAdapter(
            db_uri=config.db_uri, 
            root_dir=config.project_root
        )
        
        # 3. Initialize Nodes with the LLM
        self.metrics_node = MetricsAnalystNode(self.llm)

    def _construct_graph(self):
        workflow = StateGraph(self.state_schema)
        
        # Add Nodes
        workflow.add_node("metric_analyst", self.metrics_node.execute)
        
        # Define Flow
        workflow.set_entry_point("metric_analyst")
        workflow.add_edge("metric_analyst", END)
        
        return workflow.compile()

    def load_initial_state(self) -> MetricState:
        """
        Helper method to load data using the configured adapter 
        and return the initial state object.
        """
        print(f"[{self.name}] Loading data via Adapter...")
        try:
            df = self.adapter.get_raw_srag_data()
            return {
                "raw_data": df,
                "metrics": {}
            }
        except Exception as e:
            print(f"[{self.name}] Data Load Failed: {e}")
            raise e

    def run(self):
        """
        Main entry point to execute the workflow.
        """
        # 1. Build Graph
        app = self._construct_graph()
        # 2. Prepare State (Load Data)
        initial_state = self.load_initial_state()
        # 3. Invoke
        return app.invoke(initial_state)