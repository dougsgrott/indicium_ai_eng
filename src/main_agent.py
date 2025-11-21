# main_agent.py

import os
import operator
import logging
from pathlib import Path
from typing import TypedDict, Annotated, Sequence
from datetime import timedelta # Needed for visualization helper in main if calling directly
import sys # For adding tools directory to path if needed for testing

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
from agent_schema import AgentState, FinalReportData, ChartPaths
import agent_nodes as nodes

# Conditional Edge: Logic to decide to continue or end
def should_continue(state):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        # The agent wants to use a tool
        return "call_tool"
    # The agent is done and has a final answer
    return END


# --- Global Logging Setup ---
# Use logging instead of print() for better auditability (Governance)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SARS_Orchestrator")

# --- 1. CONFIGURATION: Load from Environment/Settings (Separation of Concerns) ---
try:
    # CRITICAL: Ensure `settings.py` is robust and handles missing variables.
    from settings import settings
except ImportError:
    # Fallback to direct environment variables if settings.py is not used
    class Settings:
        # Define necessary attributes with safe defaults
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
        # LangSmith (if required)
        LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true")
        LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
        LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
        LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "sars-poc-agent")
    settings = Settings()
    logger.warning("settings.py not found. Using direct environment variables.")

# Apply necessary environment variables (LangSmith & API keys)
if settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    logger.info(f"LangSmith Tracing Enabled for Project: {settings.LANGCHAIN_PROJECT}")

if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

# --- 2. PATHS & URIs (Using Pathlib for robustness) ---
# Use environment variables first, fall back to project structure
DB_FILENAME = "INFLUD19-26-06-2025.db"
DB_PATH = Path(os.getenv("SARS_DB_PATH", "data")) / DB_FILENAME
IMG_OUTPUT_DIR = Path(os.getenv("SARS_IMG_DIR", "static/images"))

TEMPLATE_DIR = Path(os.getenv("SARS_TEMPLATE_DIR", "reports/templates"))
REPORT_OUTPUT_DIR = Path(os.getenv("SARS_IMG_DIR", "reports/generated_reports"))

# SQLite URI must be absolute path
DB_URI = f"sqlite:///{DB_PATH.resolve()}"
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# --- 3. INITIALIZE LLM AND TOOLS (Dependency Injection) ---
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
synthesis_llm = ChatOpenAI(model=LLM_MODEL, temperature=0.1).with_structured_output(
    FinalReportData,
    method='function_calling',
)
logger.info(f"LLM initialized: {LLM_MODEL}")

try:
    # Initialize all tools
    metrics_tool = create_mock_sars_stats_tool() # Mock for determinism
    search_tool = create_mock_search_tool()      # Mock for determinism
    plot_tool = setup_visualization_tool(str(DB_PATH.resolve()), str(IMG_OUTPUT_DIR.resolve()))
    file_handler_tool = create_file_handler_tool() #str(PROJECT_ROOT)
    report_tool = setup_report_tool(str(TEMPLATE_DIR.resolve()), str(REPORT_OUTPUT_DIR.resolve()))
    
    # Inject tools into the external nodes module
    nodes.METRICS_TOOL = metrics_tool
    nodes.SEARCH_TOOL = search_tool
    nodes.PLOT_TOOL = plot_tool
    nodes.FILE_HANDLER_TOOL = file_handler_tool
    nodes.REPORT_TOOL = report_tool
    nodes.SYNTHESIS_LLM = synthesis_llm
    
except Exception as e:
    logger.critical(f"Failed to initialize one or more components: {e}")
    sys.exit(1)

# Create all necessary tools, passing configurations explicitly
# try:
#     sql_tool = create_sars_stats_tool(DB_URI, llm)
#     search_tool = create_search_tool() # Handles its own config internally (TAVILY_API_KEY)
#     plot_tool = setup_visualization_tool(str(DB_PATH.resolve()), str(IMG_OUTPUT_DIR.resolve()))
#     report_tool = setup_report_tool(str(TEMPLATE_DIR.resolve()), str(REPORT_OUTPUT_DIR.resolve()))
#     file_handler_tool = create_file_handler_tool()

#     mock_sql_tool = create_mock_sars_stats_tool()
#     mock_search_tool = create_mock_search_tool()


#     tools = [sql_tool, search_tool, plot_tool, report_tool, file_handler_tool]
#     tools = tools + [mock_sql_tool, mock_search_tool]

# except Exception as e:
#     logger.critical(f"Failed to initialize one or more tools: {e}")
#     sys.exit(1)


# --- 4. LANGGRAPH DETERMINISTIC NODE DEFINITIONS ---

logger.info("Building the deterministic agent pipeline...")
workflow = StateGraph(AgentState)

# Add the explicit function nodes from the external file
workflow.add_node("data_retrieval", nodes.execute_data_retrieval)
workflow.add_node("charts_io", nodes.execute_charts_and_read)
workflow.add_node("synthesis", nodes.execute_synthesis)
workflow.add_node("report_generation", nodes.execute_report_generation)

# Define the fixed, linear flow (maximum determinism)
workflow.set_entry_point("data_retrieval")
workflow.add_edge("data_retrieval", "charts_io")
workflow.add_edge("charts_io", "synthesis")
workflow.add_edge("synthesis", "report_generation")
workflow.add_edge("report_generation", END)

app = workflow.compile()
logger.info("Agent pipeline compiled successfully.")





# # Bind Tools to the Main Agent (The Master Agent)
# agent_llm = llm.bind_tools(tools)

# # Node 2: The node that executes the tools
# tool_node = ToolNode(tools)

# # --- Build and Compile the Graph ---
# logger.info("Building the agent graph...")
# workflow = StateGraph(AgentState)

# # Add the nodes
# workflow.add_node("agent", call_model)
# workflow.add_node("call_tool", tool_node)
# workflow.set_entry_point("agent")
# workflow.add_conditional_edges(
#     "agent",
#     should_continue,
#     {
#         "call_tool": "call_tool",
#         END: END
#     }
# )
# workflow.add_edge("call_tool", "agent")

# app = workflow.compile()
# logger.info("Agent graph compiled successfully. Ready to receive queries.")

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

# {'mortality_rate': '12.14%', 'cases_last_week': 0, 'icu_occupancy': 17375, 'vaccination_rate': '32.09%', 'charts': ['C:/Users/douglas.sgrott_indic/Documents/Projects/indicium_ai_eng/static/images/daily_30d.png', 'C:/Users/douglas.sgrott_indic/Documents/Projects/indicium_ai_eng/static/images/monthly_12m.png'], 'news': 'No good DuckDuckGo Search Result was found', 'current_date': '2025-11-18'}
