from typing import TypedDict, List, Dict

class NewsItem(TypedDict):
    title: str
    url: str
    content: str

class NewsResearcherState(TypedDict):
    news_snippets: List[Dict] # List of NewsItem
    news_analysis: str        # Raw JSON dump