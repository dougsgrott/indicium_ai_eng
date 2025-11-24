# mock_web_search_tool.py

import os
import logging
import json
from langchain_core.tools import Tool
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# --- Mock Data ---
MOCK_SEARCH_RESULTS: List[Dict[str, Any]] = [
    {
        'title': 'SARS virus - Latest research and news',
        'url': 'https://www.nature.com/subjects/sars-virus',
        'content': 'SARS virus is an infectious agent belonging to the virus family Coronaviridae, which causes severe respiratory illnesses in humans and animals. SARS (severe acute respiratory syndrome) coronavirus (CoV) is a novel member of this family that causes acute respiratory distress syndrome (ARDS), which is associated with high mortality rates.',
    },
    {
        'title': 'Severe Acute Respiratory Syndrome',
        'url': 'https://www.news-medical.net/condition/Severe-Acute-Respiratory-Syndrome',
        'content': 'SARS or Severe Acute Respiratory Syndrome is a viral respiratory illness caused by a coronavirus - the SARS associated coronavirus (SARS-CoV) - which can be life-threatening.',
    },
    {
        'title': "'Patient zero' catches SARS, the older cousin of COVID — ...",
        'url': 'https://www.livescience.com/health/viruses-infections-disease/science-history-patient-zero-catches-sars-the-older-cousin-of-covid',
        'content': 'The SARS epidemic, as scary as it was at the time, was ultimately just a dress rehearsal for the COVID-19 pandemic that swept across the globe from March 2020 to May 2023, after early cases started to emerge in November 2019.',
    },
]

# --- Factory Function ---

def create_mock_search_tool():
    """
    Creates a simulated search tool that returns fixed, pre-defined results.
    This replaces the need for the Tavily or DuckDuckGo API key during testing.
    """
    logger.info("Initializing MOCK Web Search Tool (Simulation Mode).")

    def sars_news_search_mock(query: str) -> str:
        """
        SIMULATED tool for retrieving real-time news about SARS and outbreaks. 
        Returns fixed results regardless of the query content.
        """
        logger.info(f"MOCK TOOL: Search query received: '{query[:50]}...'")
        
        # The tool returns the list structure as a string, which the agent then processes.
        # We must return the content formatted as LangChain tools often do.
        # Since the provided mock data is a list of dictionaries, we serialize it.
        
        return json.dumps(MOCK_SEARCH_RESULTS)

    # Wrap the function as a LangChain Tool object
    return Tool(
        name="sars_news_search_mock",
        func=sars_news_search_mock,
        description=(
            "SIMULATED: Use this tool to get fixed, static news articles and summaries "
            "about SARS. Returns data useful for contextualizing statistical metrics."
        )
    )

# --- DEBUGGING BLOCK ---
if __name__ == "__main__":
    # 1. Setup Logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 2. Initialize the Mock Tool
    mock_tool = create_mock_search_tool()
    
    test_query = "Explain the current severity of SARS based on news."

    print("\n--- Running MOCK Web Search Tool Debug Test ---")
    print(f"Tool Name: {mock_tool.name}")
    print(f"Test Query: {test_query}")
    
    try:
        # 3. Invoke the tool directly
        result = mock_tool.invoke(test_query)
        
        # 4. Print results (only showing the first 500 characters)
        print("\n--- Tool Result (JSON String) ---")
        print(f"Result snippet: {result[:500]}...") 
        print("-----------------------------------")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")