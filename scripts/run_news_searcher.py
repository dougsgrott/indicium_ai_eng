import os
import sys
import logging
import json
from langchain_openai import ChatOpenAI
from utils import set_path_to_imports
root_dir = set_path_to_imports()


try:
    from settings import settings
    from workflows.agents.news_researcher.node import NewsResearcherNode
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # 1. Setup
    if not settings.OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found.")
        return

    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=settings.OPENAI_API_KEY)
    
    # 2. Mock State
    # NOTE: State is empty of metrics. The agent must rely purely on System/User prompts.
    mock_state = {
        "metrics": {} 
    }

    # 3. Run Agent
    print("\n" + "="*50)
    print("STARTING NEWS RESEARCHER AGENT (NO METRICS)")
    print("="*50)
    
    try:
        node = NewsResearcherNode(llm)
        result = node.execute(mock_state)
        
        print("\n" + "="*50)
        print("OUTPUT (STATE UPDATE)")
        print("="*50)
        
        snippets = result.get("news_snippets", [])
        print(f"Found {len(snippets)} articles:\n")
        
        for i, item in enumerate(snippets, 1):
            title = item.get('title', 'No Title')
            url = item.get('url', '#')
            content = item.get('content', '')[:150].replace('\n', ' ')
            print(f"{i}. {title}")
            print(f"   URL: {url}")
            print(f"   Snippet: {content}...\n")
            
    except Exception as e:
        print(f"Execution Failed: {e}")

if __name__ == "__main__":
    main()