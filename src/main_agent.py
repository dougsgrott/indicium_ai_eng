# main_agent.py

import os
import operator
import logging
from pathlib import Path
from typing import TypedDict, Annotated, Sequence
from datetime import timedelta
import sys
from functools import partial

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

# --- Project Imports ---
from tools.sql_tool import create_sars_stats_tool
from tools.mock_sql_tool import create_mock_sars_stats_tool
from tools.web_search_tool import create_search_tool
from tools.mock_web_search_tool import create_mock_search_tool
from tools.plot_tool import setup_visualization_tool
from tools.file_handler_tool import create_file_handler_tool
from tools.report_tool import setup_report_tool
from agent_schema import AgentState, FinalReportData, ChartPaths, MetricsData
import agent_nodes as nodes

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)
from settings import settings

# Conditional Edge: Logic to decide to continue or end
def should_continue(state):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        # The agent wants to use a tool
        return "call_tool"
    # The agent is done and has a final answer
    return END


# --- Global Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SARS_Orchestrator")

# --- INITIALIZE LLM AND TOOLS (Dependency Injection) ---
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
sql_llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.OPENAI_API_KEY)
metrics_tool = create_sars_stats_tool(settings.DB_URI, sql_llm)
search_tool = create_search_tool() # Reads env var internally
plot_tool = setup_visualization_tool(settings.DB_URI, str(settings.IMG_OUTPUT_DIR))
file_tool = create_file_handler_tool()
report_tool = setup_report_tool(str(settings.TEMPLATE_DIR), str(settings.REPORT_OUTPUT_DIR))
synthesis_llm = ChatOpenAI(model=LLM_MODEL, temperature=0.1).with_structured_output(
    FinalReportData,
    method='function_calling',
)
sql_llm = ChatOpenAI(model=LLM_MODEL, temperature=0.1)

logger.info(f"LLM initialized: {LLM_MODEL}")

try:
    logger.info("Initializing Tools...")
    metrics_tool = create_sars_stats_tool(settings.DB_URI, sql_llm)
    search_tool = create_search_tool() # Reads env var internally
    plot_tool = setup_visualization_tool(settings.DB_URI, str(settings.IMG_OUTPUT_DIR))
    file_tool = create_file_handler_tool()
    report_tool = setup_report_tool(str(settings.TEMPLATE_DIR), str(settings.REPORT_OUTPUT_DIR))

except Exception as e:
    logger.critical(f"Failed to initialize one or more components: {e}")
    sys.exit(1)

# --- 4. LANGGRAPH DETERMINISTIC NODE DEFINITIONS ---

logger.info("Building the deterministic agent pipeline...")
workflow = StateGraph(AgentState)

# Add the explicit function nodes from the external file
# workflow.add_node("data_retrieval", nodes.execute_data_retrieval)
# Node: Data Retrieval (Parallel Execution Logic inside node)
workflow.add_node(
    "data_retrieval",
    lambda state: {
        **nodes.retrieve_metrics(state, metrics_tool),
        **nodes.retrieve_news(state, search_tool)
    }
)
workflow.add_node("charts_io", partial(nodes.generate_charts, plot_tool=plot_tool, file_tool=file_tool))
workflow.add_node("synthesis", partial(nodes.synthesize_report, synthesis_llm=synthesis_llm))
workflow.add_node("report_generation", partial(nodes.execute_report_generation, report_tool=report_tool))

# Define the fixed, linear flow (maximum determinism)
workflow.set_entry_point("data_retrieval")
workflow.add_edge("data_retrieval", "charts_io")
workflow.add_edge("charts_io", "synthesis")
workflow.add_edge("synthesis", "report_generation")
workflow.add_edge("report_generation", END)

app = workflow.compile()
logger.info("Agent pipeline compiled successfully.")

# --- 5. EXECUTION ---
def run_query(query: str):
    logger.info(f"\n--- Query: {query} ---")
    
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "charts_html": {},
        "metrics_json": "",
        "news_snippets": [],
        "final_report_json_str": ""
    }

    # We stream the events to see the agent's thought process
    final_output = None
    for event in app.stream(initial_state, {"recursion_limit": 10}):
        for key, value in event.items():
            if key not in [END, START]:
                logger.info(f"[{key.upper()}]: State Updated.")
            
            if key == END:
                final_output = value['messages'][-1].content

    logger.info("--- Done ---")
    return final_output

# --- Example Queries ---
if __name__ == "__main__":
    # Test all tools
    # run_query("Calculate the mortality rate and rate of increase in cases. Then, use the news to explain the current trend.")

    # Mock
    # run_query("Calculate the mortality rate and rate of increase in cases but use mock the results.")

    # Test Plotting and Metrics
    # run_query("First, calculate the ICU occupancy rate. Then, generate the daily case chart for the last 30 days.")

    # run_query("Latest SARS outbreak news Brazil 2024")

    run_query("Create a report with the metrics, visualizations and news regarding SARS.")

    # # Compile the graph
    # app = workflow.compile()
    # logger.info("Agent pipeline compiled successfully.")

    # # --- Visualization Step ---
    # try:
    #     # Generates a graph object from the workflow
    #     graph_obj = app.get_graph() 
        
    #     # Draw the graph and save it to a file
    #     # Use 'png' for documentation, 'svg' for web viewing (if supported)
    #     graph_obj.draw_png("sars_pipeline_graph.png")
    #     logger.info("Graph visualization saved as sars_pipeline_graph.png")
    # except ImportError:
    #     logger.warning("Graphviz is not installed. Skipping graph visualization.")
    # except Exception as e:
    #     logger.error(f"Error drawing graph: {e}")