# agent_nodes.py

import os
import logging
import json
from langchain_core.messages import HumanMessage
from typing import Dict, Any
import re

from tools.sql_tool import create_sars_stats_tool
from tools.mock_sql_tool import create_mock_sars_stats_tool 
from tools.web_search_tool import create_search_tool
from tools.mock_web_search_tool import create_mock_search_tool
from tools.plot_tool import setup_visualization_tool
from tools.file_handler_tool import create_file_handler_tool
from tools.report_tool import setup_report_tool
from agent_schema import AgentState, FinalReportData, NewsSnippet

logger = logging.getLogger("SARS_Nodes")

def retrieve_metrics(state: AgentState, metrics_tool):
    # Check for mock tool implementation preference here if needed, otherwise use METRICS_TOOL
    prompt = """
    Calculate the following 4 metrics based on the 'srag_records' table:
    1. Mortality Rate
    2. ICU Occupancy Rate
    3. Vaccination Rate
    4. Rate of Increase (last 7 days vs previous 7 days)

    RETURN ONLY A JSON OBJECT. Do not explain. Format:
    {
      "mortality_rate": "XX.X%",
      "icu_occupancy": "XX.X%",
      "vaccination_rate": "XX.X%",
      "rate_of_increase": "XX.X%"
    }
    """

    raw_output = metrics_tool.invoke(prompt)

    try:
        # Search for the first occurrence of a JSON dictionary in the output string
        match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if match:
            metrics_data = json.loads(match.group(0))
            metrics_json = json.dumps(metrics_data)
        else:
            logger.error("SQL Agent output did not contain a valid JSON object.")
            # If JSON is not found, default to a structured error state
            # metrics_json_str = json.dumps({"error": "Failed to extract metrics JSON"})
            raise ValueError("No JSON found in SQL Agent output.")
    except Exception as e:
        logger.error(f"Failed to parse SQL output JSON: {e}")
        # metrics_json_str = json.dumps({"error": "Failed to parse metrics JSON"})
        metrics_json = json.dumps({
            "mortality_rate": "N/A", "icu_occupancy": "N/A", 
            "vaccination_rate": "N/A", "rate_of_increase": "N/A",
            "error": str(e)
        })

    return {
        "metrics_json": metrics_json,
        "messages": [HumanMessage(content="Metrics retrieval complete.")]
    }


def retrieve_news(state: AgentState, search_tool):
    news_data_list = search_tool.invoke("Current SARS news context.")
    try:
        # news_list = json.loads(news_data_list) # MOCK
        news_list = news_data_list
        # Handle case where mock search returns a simple string (error/fallback)
        if isinstance(news_list, dict) and 'title' in news_list:
            news_list = [news_list]
        elif not isinstance(news_list, list):
            # news_list = [{"content": news_data_list, "title": "Search Error/Fallback"}]
            news_list = [{"title": "Search Result", "url": "#", "content": news_list}]

    except json.JSONDecodeError:
        logger.warning("News tool returned non-JSON string. Using raw string as content.")
        news_list = [{"content": news_data_list, "title": "Raw Search Output"}]
    return {"news_snippets": news_list}
    # return news_list


def generate_charts(state: AgentState, plot_tool, file_tool) -> Dict[str, Any]:
    """Node B: Generates plots and reads their HTML content."""
    logger.info("NODE B: Generating Visualization Artifacts.")
    
    charts_content = {}
    
    for chart_type in ['daily_30d', 'monthly_12m']:
        try:
            # 1. Generate Chart (Returns file path string)
            result_msg = plot_tool.invoke(chart_type)
            
            if "Success" in result_msg:
                # Extract path from message: "Success: Chart saved to /path/to/file.html"
                file_path = result_msg.split(" to ")[-1].strip()
                
                # 2. Read Content
                html_content = file_tool.invoke(file_path)
                charts_content[f"{chart_type}_html"] = html_content
            else:
                logger.warning(f"Plot tool failed for {chart_type}: {result_msg}")
                charts_content[f"{chart_type}_html"] = f"<!-- Chart Generation Failed: {result_msg} -->"
                
        except Exception as e:
            logger.error(f"Error processing chart {chart_type}: {e}")
            charts_content[f"{chart_type}_html"] = f"<!-- Error: {e} -->"

    return {
        "charts_html": charts_content,
        "messages": [HumanMessage(content="Charts generated.")]
    }


def synthesize_report(state: AgentState, synthesis_llm) -> Dict[str, Any]:
    """Node C: Synthesizes data into final JSON structure using the LLM (Pydantic enforced)."""
    logger.info("NODE C: Synthesizing data into final JSON structure (LLM Call).")
    
    # 1. Prepare raw input data for the LLM prompt
    metrics = state.get("metrics_json", "{}")
    news = state.get("news_snippets", [])
    news_summary = json.dumps(
        [{"title": n.get('title'), "content": n.get('content')[:200]} for n in news], 
        indent=2
    )
    
    prompt = f"""
    You are a Health Data Analyst. Generate a report JSON based on:
    
    1. METRICS: {metrics}
    2. NEWS CONTEXT: {news_summary}
    
    TASKS:
    - Analyze the metrics.
    - Use news to explain trends (e.g., why cases are rising).
    - Provide a professional summary.
    - Strict adherence to the schema.
    """

    try:
        # LLM returns a Pydantic object (FinalReportData)
        report_data: FinalReportData = synthesis_llm.invoke(prompt)
        
        # INJECT RAW DATA (Preserve fidelity)
        # 1. Inject full HTML charts (LLM doesn't handle massive HTML strings well)
        report_data.charts.daily_30d_html = state['charts_html'].get('daily_30d_html', '')
        report_data.charts.monthly_12m_html = state['charts_html'].get('monthly_12m_html', '')
        
        # 2. Inject structured news (ensure URLs are preserved)
        valid_news = [
            NewsSnippet(title=n.get('title', 'No Title'), url=n.get('url', '#'), content=n.get('content', ''))
            for n in news if isinstance(n, dict)
        ]
        report_data.commentary.news_sources = valid_news

        return {
            "final_report_json_str": report_data.model_dump_json(),
            "messages": [HumanMessage(content="Synthesis complete.")]
        }
        
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return {"final_report_json_str": "{}", "messages": [HumanMessage(content="Synthesis Failed.")]}


def execute_report_generation(state: AgentState, report_tool) -> Dict[str, Any]:
    """Node D: Executes the Final Report Generation Tool (Deterministic tool call)."""
    logger.info("NODE D: Executing Final Report Generation Tool.")

    final_json = state["final_report_json_str"]    
    report_tool_result = report_tool.invoke(final_json)
    return {
        "messages": [HumanMessage(content=report_tool_result)]
    }
