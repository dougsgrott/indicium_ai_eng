# sql_tool.py

import os
import logging
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

SARS_AGENT_PROMPT_SUFFIX = """
You are a specialized Data Analyst for the Brazilian SARS (SRAG) database.
The table name is 'srag_records'.

CRITICAL DATA DICTIONARY & CODES:
1. **Dates**: Use 'DT_NOTIFIC' for all time-series analysis. Format is YYYY-MM-DD.
2. **Outcomes (EVOLUCAO)**:
   - 1: Cure/Discharge
   - 2: Death (Use this for Mortality Rate)
   - 3: Death from other causes
   - 9 or Null: Ignored/Under Treatment (Exclude these from denominators)
3. **ICU (UTI)**:
   - 1: Yes (Admitted to ICU)
   - 2: No
   - 9 or Null: Ignored
4. **Vaccination (VACINA)**:
   - 1: Yes
   - 2: No
   - 9 or Null: Ignored

METRIC CALCULATION RULES:
- **Mortality Rate**: (Count(EVOLUCAO=2) / Count(EVOLUCAO IN (1, 2, 3))) * 100.
- **ICU Rate**: (Count(UTI=1) / Count(UTI IN (1, 2))) * 100.
- **Rate of Increase**: Compare count of cases in the last 7 days vs the previous 7 days.
- **Vaccination Rate**: (Count(VACINA=1) / Count(VACINA IN (1, 2))) * 100.

Start by checking the table schema if you are unsure. 
Always return the final answer as a concise summary of the requested metric.
"""

def create_sars_stats_tool(db_uri: str, llm: ChatOpenAI):
    """
    Creates a specialized SQL agent tool for querying SARS/SRAG data.
    
    Args:
        db_uri (str): Connection string (e.g., 'sqlite:///sars_data.db')
        llm (ChatOpenAI): The language model instance
    """
    logger.info(f"Initializing SARS Data Agent... (Connecting to: {db_uri})")
    
    try:
        db = SQLDatabase.from_uri(db_uri)
    except Exception as e:
        logger.critical(f"Failed to connect to database at {db_uri}: {e}")
        raise # Critical error, stop tool initialization

    sql_agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=True,
        suffix=SARS_AGENT_PROMPT_SUFFIX
    )

    @tool
    def sars_database_stats(query: str) -> str:
        """
        Useful for calculating statistical metrics (Mortality, ICU occupancy, Vaccination rates) 
        and case counts from the SARS/SRAG database. 
        Input should be a specific question like 'What is the mortality rate?' or 
        'How many cases last week?'.
        """
        try:
            logger.info(f"Executing SQL query command for: {query[:50]}...")
            response = sql_agent_executor.invoke({"input": query})
            return response["output"]
        except Exception as e:
            logger.error(f"Error during SQL Agent execution for query '{query[:50]}...': {e}")
            return f"Error querying database: {str(e)}"

    return sars_database_stats


# ----------------------------------------------------------------------
# DEBUGGING BLOCK: Allows tool to be run independently for testing.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Configuration (MOCK VALUES/ENV VARS)
    # NOTE: You must set your OPENAI_API_KEY environment variable.
    DB_FILE = os.getenv("SARS_DB_URI", "sqlite:///./data/INFLUD19-26-06-2025.db")
    
    # Initialize Components
    try:
        test_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        sars_tool = create_sars_stats_tool(DB_FILE, test_llm)
        test_query = "What is the mortality rate among closed cases?"
        
        print("\n--- Running SQL Agent Debug Test ---")
        print(f"Query: {test_query}")
        result = sars_tool.invoke(test_query)
        
        print("\n--- Agent Result ---")
        print(result)
        print("--------------------")
        
    except Exception as e:
        print(f"Error: {e}")