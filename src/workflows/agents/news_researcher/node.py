import json
import logging
from nodes.base import BaseNode
from .prompts import SYSTEM_PROMPT, SEARCH_QUERY_PROMPT
from tools.web_search_tool import create_search_tool

logger = logging.getLogger(__name__)

class NewsResearcherNode(BaseNode):
    def __init__(self, llm):
        super().__init__(llm, "NewsResearcher")
        self.search_tool = create_search_tool()

    def execute(self, state: dict) -> dict:
        # Note: We intentionally DO NOT fetch 'metrics' from state here.
        # The search is based on the general domain context, not specific numbers.
        
        # 1. Generate Targeted Search Query
        # We ask the LLM to formulate the best query for "current situation"
        try:
            search_query = self._invoke_llm(SYSTEM_PROMPT, SEARCH_QUERY_PROMPT).strip().replace('"', '')
        except Exception as e:
            logger.warning(f"LLM Query Generation failed: {e}. Using default.")
            search_query = "SRAG Brasil surto casos recentes vacinação"

        print(f"[{self.name}] Executing Search for: '{search_query}'")

        # 2. Execute Search (Tool Step)
        try:
            raw_output = self.search_tool.invoke(search_query)
            
            # 3. Parse Output
            try:
                if isinstance(raw_output, str):
                    news_list = json.loads(raw_output)
                else:
                    news_list = raw_output
                
                # Normalize to List[Dict]
                if isinstance(news_list, dict):
                    news_list = [news_list]
                elif not isinstance(news_list, list):
                    news_list = [{"title": "Search Result", "url": "#", "content": str(raw_output)}]
                    
            except json.JSONDecodeError:
                logger.warning("News tool returned non-JSON string. Wrapping raw content.")
                news_list = [{"title": "Raw Search Output", "url": "#", "content": str(raw_output)}]
                
        except Exception as e:
            logger.error(f"Search Tool Execution Failed: {e}")
            news_list = [{"title": "Error", "url": "#", "content": f"Search failed: {str(e)}"}]

        print(f"[{self.name}] Retrieved {len(news_list)} snippets.")
        
        # 4. Update State
        # We return ONLY the snippets. 
        # We do not perform synthesis/analysis here (Metrics are unknown).
        # The 'ReportWriter' or a downstream agent will handle the correlation.
        return {
            "news_snippets": news_list,
            # We provide a raw dump for legacy compatibility if something expects 'news_analysis' string
            "news_analysis": json.dumps(news_list, indent=2) 
        }