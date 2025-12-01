from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# Import Domain Components
from .agents.chart_calculator.node import ChartCalculatorNode
from .agents.chart_calculator.states import ChartState

# Import Infrastructure
from internal.data_retrieval.adapters.sqlite_loader import SqliteSragAdapter
from .workflow_config import MetricConfig # Reusing the existing generic config

class ChartCalculatorWorkflow:
    name = "ChartCalculator"
    description = "Calculate time-series data for charts using SQL Agent"

    def __init__(self, config: MetricConfig):
        self.config = config
        self.state_schema = ChartState
        
        # 1. Initialize Infrastructure
        self.llm = ChatOpenAI(
            model=config.llm_model, 
            temperature=config.temperature,
            api_key=config.openai_api_key.get_secret_value()
        )
        
        # 2. Initialize Data Adapter
        self.adapter = SqliteSragAdapter(
            db_uri=config.db_uri, 
            root_dir=config.project_root
        )
        
        # 3. Initialize Node
        self.chart_node = ChartCalculatorNode(self.llm)

    def _construct_graph(self):
        workflow = StateGraph(self.state_schema)
        
        # Add Node
        workflow.add_node("chart_calculator", self.chart_node.execute)
        
        # Define Flow
        workflow.set_entry_point("chart_calculator")
        workflow.add_edge("chart_calculator", END)
        
        return workflow.compile()

    def load_initial_state(self) -> ChartState:
        """
        Loads data via adapter and sets default flags.
        """
        print(f"[{self.name}] Loading data via Adapter...")
        try:
            df = self.adapter.get_raw_srag_data()
            return {
                "raw_data": df,
                "include_charts": True,
                "chart_data": {}
            }
        except Exception as e:
            print(f"[{self.name}] Data Load Failed: {e}")
            raise e

    def run(self):
        """Execute the workflow."""
        app = self._construct_graph()
        initial_state = self.load_initial_state()
        return app.invoke(initial_state)