# agent_nodes.py
# Contains all the deterministic function logic for the workflow.
# This file houses all the processing logic, including the single LLM call for synthesis.

import os
import logging
import json
from langchain_core.messages import HumanMessage
from typing import Dict, Any

from tools.sql_tool import create_sars_stats_tool
from tools.mock_sql_tool import create_mock_sars_stats_tool 
from tools.web_search_tool import create_search_tool
from tools.mock_web_search_tool import create_mock_search_tool
from tools.plot_tool import setup_visualization_tool
from tools.file_handler_tool import create_file_handler_tool
from tools.report_tool import setup_report_tool
from agent_schema import AgentState, FinalReportData, NewsSnippet # Import state and schema

logger = logging.getLogger("SARS_Nodes")

# --- GLOBAL TOOL HANDLERS (To be set by main_agent.py) ---
# These variables hold the instantiated tool objects passed from the main script.
METRICS_TOOL = None
SEARCH_TOOL = None
PLOT_TOOL = None
FILE_HANDLER_TOOL = None
REPORT_TOOL = None
SYNTHESIS_LLM = None

# --- NODE DEFINITIONS (Deterministic Functions) ---

def execute_data_retrieval(state: AgentState) -> Dict[str, Any]:
    """Node A: Executes Metrics and News Retrieval (Deterministic)."""
    logger.info("NODE A: Retrieving Metrics and News.")
    
    # Check for mock tool implementation preference here if needed, otherwise use METRICS_TOOL
    metrics_json_str = METRICS_TOOL.invoke("Calculate all metrics.")
    news_json_str = SEARCH_TOOL.invoke("Current SARS news context.")
    
    try:
        news_list = json.loads(news_json_str)
        # Handle case where mock search returns a simple string (error/fallback)
        if isinstance(news_list, dict) and 'title' in news_list:
             news_list = [news_list]
        elif not isinstance(news_list, list):
             news_list = [{"content": news_json_str, "title": "Search Error/Fallback"}]

    except json.JSONDecodeError:
        logger.warning("News tool returned non-JSON string. Using raw string as content.")
        news_list = [{"content": news_json_str, "title": "Raw Search Output"}]
    
    return {
        "metrics_json": metrics_json_str,
        "news_snippets": news_list,
        "messages": [HumanMessage(content="Data retrieval complete.")] 
    }

def execute_charts_and_read(state: AgentState) -> Dict[str, Any]:
    """Node B: Generates Plots, Reads HTML Content, and isolates large data."""
    logger.info("NODE B: Generating Plots and Reading HTML Content.")
    
    # 1. Execute Plotting (Tool returns file paths)
    daily_path_msg = PLOT_TOOL.invoke("daily_30d")
    monthly_path_msg = PLOT_TOOL.invoke("monthly_12m")
    
    # 2. Extract paths from the success message ("Success: Chart saved to C:/path/file.html")
    daily_path = daily_path_msg.split(' to ')[-1].strip('.')
    monthly_path = monthly_path_msg.split(' to ')[-1].strip('.')
    
    # 3. Read HTML Content using the file handler tool (This is where the massive string is returned)
    daily_html = FILE_HANDLER_TOOL.invoke(daily_path)
    monthly_html = FILE_HANDLER_TOOL.invoke(monthly_path)
    
    # 4. Consolidate into structured dict (This data is NOT appended to messages)
    charts_html_dict = {
        "daily_30d_html": daily_html,
        "monthly_12m_html": monthly_html,
    }
    
    # The large data is placed directly into the structured state keys.
    return {
        "charts_html": charts_html_dict,
        "messages": [HumanMessage(content="Charts generated and HTML content loaded.")]
    }

def execute_synthesis(state: AgentState) -> Dict[str, Any]:
    """Node C: Synthesizes data into final JSON structure using the LLM (Pydantic enforced)."""
    logger.info("NODE C: Synthesizing data into final JSON structure (LLM Call).")
    
    # 1. Prepare raw input data for the LLM prompt
    
    # Metrics JSON string needs to be parsed before being presented to the LLM
    try:
        # Use json.loads for resilience, providing a default structure on failure
        metrics_data = json.loads(state['metrics_json'])
    except:
        metrics_data = {"error": "Invalid metrics JSON"}

    # Chart data is already in dictionary format (charts_html)
    charts_data = state['charts_html']
    
    structured_news_list = [
        NewsSnippet(**snippet)
        for snippet in state['news_snippets'] if all(k in snippet for k in ['title', 'url', 'content'])
    ]

    # Generate the JSON string of the news list for the prompt
    news_json_for_prompt = json.dumps([s.model_dump() for s in structured_news_list], indent=2)

    # CRITICAL FIX: The prompt should NOT contain the full HTML strings.
    # It should only summarize the availability of the charts.
    prompt_content = f"""
    You are the final report synthesizer. Your task is to process the available data and structure it precisely according to the required JSON schema (FinalReportData).
    
    1. **Metrics (JSON):** {json.dumps(metrics_data, indent=2)}
    2. **News Snippets (Structured Input):** The exact, structured list of news articles is provided below. {news_json_for_prompt}
    3. **Charts:** The raw HTML content for the charts has been loaded and is available in the Python state.
    
    Your primary job is to write the 'commentary.summary' synthesizing the metrics and news. You MUST embed the full HTML content from the chart state variables into the final Pydantic object under the 'charts' key.
    
    ---
    
    **INSTRUCTIONS FOR JSON STRUCTURE:**
    * You MUST embed the **entire list** from **Section 2 (News Snippets)** directly into the 'commentary.news_sources' field of your output. Do not omit any items, and maintain the exact structure (title, url, content).
    * Use **placeholders** for the HTML content (e.g., 'CHART_DAILY_PLACEHOLDER') which will be replaced by Python.
    """
    # * Use the **News Snippets** list provided above directly in the 'commentary.news_sources' field of your output.



    # 2. Invoke LLM (response_object is the FinalReportData Pydantic instance)
    response_object = SYNTHESIS_LLM.invoke(prompt_content)

    # 3. POST-PROCESSING: Inject the actual HTML content    
    final_report_data = response_object 

    # --- INJECTION 1: Charts (High Volume Data) ---
    # Inject the actual HTML content from the state back into the structured data
    # This replaces the LLM's placeholder/empty string with the actual content.
    final_report_data.charts.daily_30d_html = charts_data.get('daily_30d_html', 'Chart Content Not Found')
    final_report_data.charts.monthly_12m_html = charts_data.get('monthly_12m_html', 'Chart Content Not Found')

    # --- INJECTION 2: News Snippets (Data integrity fix) ---
    pure_dict_news_list = [item.model_dump() for item in structured_news_list]
    final_report_data.commentary.news_sources = pure_dict_news_list

    # 4. Convert the fixed Pydantic object back into a raw JSON string required by the report tool
    final_json_str = final_report_data.json() 
    
    return {
        "final_report_json_str": final_json_str,
        "messages": [HumanMessage(content="Synthesis complete, final JSON generated.")]
    }

def execute_report_generation(state: AgentState) -> Dict[str, Any]:
    """Node D: Executes the Final Report Generation Tool (Deterministic tool call)."""
    logger.info("NODE D: Executing Final Report Generation Tool.")
    
    final_json = state["final_report_json_str"]
    
    # The tool is invoked directly with the structured JSON string.
    report_tool_result = REPORT_TOOL.invoke(final_json)
    
    return {
        "messages": [HumanMessage(content=report_tool_result)]
    }