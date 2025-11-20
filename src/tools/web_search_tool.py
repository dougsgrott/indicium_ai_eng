# web_search_tool.py

import os
import sys
import logging
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import Tool

logger = logging.getLogger(__name__)

# NOTE: The tool now relies ONLY on the OS environment variables 
# (TAVILY_API_KEY) being set externally by main_agent.py.

def create_search_tool():
    """
    Factory function that returns the best available search tool for SARS news.
    
    Strategy: Tries to use Tavily (API Key needed), falls back to DuckDuckGo (Free).
    """
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    if tavily_key:
        logger.info("Initializing Tavily Search Tool (Optimized for AI)...")
        search_tool = TavilySearchResults(
            max_results=5,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False 
        )
        
        # Customizing metadata for the SARS context
        search_tool.name = "sars_news_search"
        search_tool.description = (
            "A search engine optimized for retrieving real-time news about SARS, "
            "COVID-19, and influenza outbreaks. "
            "Use this to find qualitative explanations for statistical trends "
            "(e.g., 'Why did cases spike in March 2024?')."
        )
        return search_tool

    else:
        logger.warning("TAVILY_API_KEY not found. Falling back to DuckDuckGo.")
        ddg_search = DuckDuckGoSearchRun()
        
        # Wrap DDG in a custom Tool to enforce the healthcare context
        return Tool(
            name="sars_news_search",
            func=ddg_search.run,
            description=(
                "Search for current news regarding SARS, hospital occupancy, and vaccination campaigns. "
                "Use this when the user asks for 'reasons', 'news', or 'context' behind the data."
            )
        )


# --- Usage Test ---
if __name__ == "__main__":

    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sys.path.insert(0, parent_dir)

    # This block only runs if you execute the script directly
    tool = create_search_tool()
    
    print(f"\nTesting tool: {tool.name}")
    query = "Latest SARS outbreak news Brazil 2024"
    
    try:
        result = tool.invoke(query)
        print(f"Result snippet: {str(result)[:300]}...") 
    except Exception as e:
        print(f"Tool execution failed: {e}")
