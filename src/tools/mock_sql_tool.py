# mock_sql_tool.py

import os
import logging
import json
import random
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

def create_mock_sars_stats_tool():
    """
    Creates a simulated SQL tool that returns fixed metric values 
    instead of running the LangChain SQL Agent. Used for accelerating 
    development when the database or LLM is unavailable.
    """
    logger.info("Initializing MOCK SARS Data Tool (Simulation Mode).")

    # Define the fixed, simulated metric values
    SIMULATED_METRICS = {
        'mortality_rate': '12.14%',
        'cases_last_week': 0,
        'icu_occupancy': 17375,
        'vaccination_rate': '32.09%',
        # Use dynamic values for rate of increase to show responsiveness
        'rate_of_increase': f'{round(random.uniform(3.0, 7.0), 2)}%',
        'cases_this_week': random.randint(100, 500)
    }

    @tool
    def sars_database_stats_mock(query: str) -> str:
        """
        SIMULATED tool for calculating statistical metrics (Mortality, ICU occupancy, Vaccination rates) 
        and case counts from the SARS/SRAG database. 
        Returns fixed or semi-fixed values for rapid testing of the agent's logic.
        """
        logger.info(f"MOCK TOOL: Processing query '{query[:50]}...'")
        
        # 1. Check for specific metric keywords in the query
        query = query.lower()
        
        if "mortality rate" in query:
            result = f"The mortality rate is {SIMULATED_METRICS['mortality_rate']}."
        elif "icu" in query or "occupancy" in query:
            result = f"The ICU occupancy count is {SIMULATED_METRICS['icu_occupancy']} patients."
        elif "vaccination rate" in query:
            result = f"The vaccination rate is {SIMULATED_METRICS['vaccination_rate']}."
        elif "increase" in query or "cases" in query or "rate" in query:
            result = f"The rate of increase is {SIMULATED_METRICS['rate_of_increase']}, with {SIMULATED_METRICS['cases_this_week']} new cases this week."
        else:
            # 2. Default: If the query is complex (e.g., "calculate all metrics"), return the full set as JSON
            result = json.dumps({
                'mortality_rate': SIMULATED_METRICS['mortality_rate'],
                'icu_occupancy': SIMULATED_METRICS['icu_occupancy'],
                'vaccination_rate': SIMULATED_METRICS['vaccination_rate'],
                'rate_of_increase': SIMULATED_METRICS['rate_of_increase'],
                'cases_this_week': SIMULATED_METRICS['cases_this_week']
            })
            
        logger.info(f"MOCK TOOL: Returning result for '{query[:50]}...': {result[:50]}...")
        return result

    return sars_database_stats_mock

# --- DEBUGGING BLOCK ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    mock_tool = create_mock_sars_stats_tool()
    
    print("\n--- Running MOCK SQL Agent Debug Test ---")
    
    # Test 1: Specific metric lookup (Should return simple string)
    # test_query_mortality = "What is the current mortality rate?"
    # print(f"\nQuery 1: {test_query_mortality}")
    # result_mortality = mock_tool.invoke(test_query_mortality)
    # print(f"Result 1: {result_mortality}")
    
    # Test 2: Complex request (Should return JSON string with all metrics)
    test_query_all = "Calculate all available metrics and return them in JSON format."
    print(f"\nQuery 2: {test_query_all}")
    result_all = mock_tool.invoke(test_query_all)
    print(f"Result 2: {result_all}")