# src/workflows/srag_conditional_workflow.py

import os
from typing import TypedDict, Dict, Any, List, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
import operator
from langfuse.langchain import CallbackHandler

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

try:
    from langfuse.langchain import CallbackHandler
    LANGFUSE_INSTALLED = True
except ImportError:
    LANGFUSE_INSTALLED = False
    # Define a dummy class to prevent NameError if used in type hinting (optional)
    CallbackHandler = None

# --- Routing Logic for Parallel Execution ---
def route_based_on_intent(state: SragWorkflowState) -> List[str]:
    """
    Determines which branches to run in parallel based on intent.
    Returns a list of node names to execute simultaneously.
    """
    next_nodes = []
    
    if state.get("include_metrics"):
        next_nodes.append("metrics_analyst")
    
    if state.get("include_charts"):
        next_nodes.append("chart_calculator")
        
    if state.get("include_news"):
        next_nodes.append("news_researcher")

    if not next_nodes:
        return ["report_maker"]
        
    return next_nodes


def barrier_check(state: SragWorkflowState) -> str:
    """
    The Gatekeeper: Checks if all 3 parallel branches have reported in.
    """
    completed = state.get("branches_completed", [])
    expected = state.get("expected_count", 0)
    print(f"[Barrier] Branches finished so far: {completed}")
    
    # Check if we have 3 unique completion markers
    # (Using set len to avoid duplicates if a node accidentally runs twice)
    if len(set(completed)) >= expected:
        return "synthesis_agent"
    
    # If not all done, this specific thread ends here.
    # The state is preserved for the next thread to check.
    return END

# --- Marker Nodes (Lightweight State Updaters) ---
# These run at the end of each branch to signal completion.

def mark_metrics_done(state):
    return {"branches_completed": ["metrics"]}

def mark_news_done(state):
    return {"branches_completed": ["news"]}

def mark_charts_done(state):
    return {"branches_completed": ["charts"]}

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
        self.intent_node = IntentNode(self.llm)
        self.metrics_node = MetricsAnalystNode(self.llm)
        self.calc_node = ChartCalculatorNode(self.llm)
        self.design_node = ChartDesignerNode(self.llm)
        self.news_node = NewsResearcherNode(self.llm)
        self.synth_node = SynthesisNode(self.llm)
        self.maker_node = ReportMakerNode(self.report_tool)

    def _construct_graph(self):
        def dispatcher_logic(state):
            count = 0
            if state.get("include_metrics"): count += 1
            if state.get("include_charts"): count += 1
            if state.get("include_news"): count += 1
            print(f"[Dispatcher] Preparing for {count} parallel tasks.")
            return {"expected_count": count}

        workflow = StateGraph(SragWorkflowState)
        
        # --- Add Nodes ---
        # workflow.add_node("intent", self.intent_node.execute)
        workflow.add_node("intent_agent", self.intent_node.execute)
        workflow.add_node("dispatcher", dispatcher_logic)

        workflow.add_node("metrics_analyst", self.metrics_node.execute)
        workflow.add_node("chart_calculator", self.calc_node.execute)
        workflow.add_node("chart_designer", self.design_node.execute)
        workflow.add_node("news_researcher", self.news_node.execute)

        # Marker Nodes (For Synchronization)
        workflow.add_node("mark_metrics", mark_metrics_done)
        workflow.add_node("mark_news", mark_news_done)
        workflow.add_node("mark_charts", mark_charts_done)

        workflow.add_node("synthesis_agent", self.synth_node.execute)
        workflow.add_node("report_maker", self.maker_node.execute)



        # --- Define Flow ---
        # Start -> Intent -> Dispatcher
        workflow.set_entry_point("intent_agent")
        workflow.add_edge("intent_agent", "dispatcher")

        # Fan-Out: Dispatcher -> All Workers Parallel
        workflow.add_conditional_edges(
            "dispatcher",
            route_based_on_intent,
            [
                "metrics_analyst", 
                "chart_calculator", 
                "news_researcher",
                "report_maker" # Fallback
            ]
        )

        # Destination: Mark nodes
        workflow.add_edge("metrics_analyst", "mark_metrics") 
        workflow.add_edge("chart_calculator", "chart_designer") 
        workflow.add_edge("chart_designer", "mark_charts")
        workflow.add_edge("news_researcher", "mark_news")

        # Fan-In (The Synchronization Barrier)
        # All marker nodes point to the Conditional Edge "barrier_check"
        workflow.add_conditional_edges(
            "mark_metrics",
            barrier_check,
            ["synthesis_agent", END]
        )
        workflow.add_conditional_edges(
            "mark_news",
            barrier_check,
            ["synthesis_agent", END]
        )
        workflow.add_conditional_edges(
            "mark_charts",
            barrier_check,
            ["synthesis_agent", END]
        )

        # Synthesis -> Report Assembly -> END
        workflow.add_edge("synthesis_agent", "report_maker")
        workflow.add_edge("report_maker", END)
        return workflow.compile()

    def _get_callbacks(self):
        """
        Safely initializes Langfuse only if enabled, configured, and installed.
        """
        callbacks = []

        # 1. Check Configuration Flag (Fastest check)
        if not self.config.langfuse_enabled:
            return callbacks

        # 2. Check if Library is Installed
        if not LANGFUSE_INSTALLED:
            print(f"[{self.name}] ⚠️ Config enabled Langfuse, but 'langfuse' package is not installed.")
            print(f"[{self.name}]    Run: pip install langfuse")
            return callbacks

        # 3. Check for Credentials
        if self.config.LANGFUSE_PUBLIC_KEY and self.config.LANGFUSE_SECRET_KEY:
            try:
                print(f"[{self.name}] 🔍 Initializing Langfuse Tracing...")
                # v3: Automatically reads from os.environ, which settings.py populated
                handler = CallbackHandler()
                callbacks.append(handler)
            except Exception as e:
                print(f"[{self.name}] ⚠️ Langfuse Init Failed: {e}")
        else:
            print(f"[{self.name}] ⚠️ Langfuse enabled but keys missing in .env")

        return callbacks

    def load_data(self):
        """Helper to fetch data using the adapter before starting the graph."""
        print(f"[{self.name}] Loading Clinical Data...")
        try:
            return self.adapter.get_raw_srag_data()
        except Exception as e:
            print(f"[{self.name}] Data Load Error: {e}")
            raise e

    def run(self, user_prompt: str=""):
        """Main execution method."""
        # 1. Prepare Data
        df = self.load_data()
        
        # 2. Define Initial State
        initial_state = {
            "user_prompt": user_prompt,
            "raw_data": df,
            "include_metrics": False,
            "include_charts": False,
            "include_news": False,
            "metrics": {},
            "chart_data": {},
            "charts_html": {},
            "news_snippets": [],
            "synthesis_result": {},
            "branches_completed": []
        }
        
        # 3. Execute Graph
        run_config = {}
        callbacks = self._get_callbacks()
        if callbacks:
            run_config["callbacks"] = callbacks

        print(f"[{self.name}] Starting Workflow Graph...")
        app = self._construct_graph()
        result = app.invoke(initial_state, config=run_config)
        
        return result
