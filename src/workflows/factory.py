import os
import sys
from langchain_openai import ChatOpenAI

# Ensure 'src' is in path for internal imports
current_file = os.path.abspath(__file__)
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
if src_dir not in sys.path:
    sys.path.append(src_dir)

try:
    from settings import settings
    from workflows.workflow_config import Config
    from internal.data_retrieval.adapters.sqlite_loader import SqliteSragAdapter
except ImportError as e:
    raise ImportError(f"Factory Import Error: {e}. Check PYTHONPATH.")

class WorkflowFactory:
    """
    Centralized factory for bootstrapping workflows.
    Reduces boilerplate in runner scripts.
    """
    
    @staticmethod
    def get_config() -> Config:
        # Determine project root (3 levels up from this file)
        root_dir = src_dir #os.path.dirname(src_dir)
        
        return Config(
            openai_api_key=settings.OPENAI_API_KEY,
            db_uri=settings.DB_URI,
            project_root=root_dir,
            llm_model="gpt-4o",

            langfuse_enabled=settings.LANGFUSE_ENABLED,
            LANGFUSE_SECRET_KEY=settings.LANGFUSE_SECRET_KEY,
            LANGFUSE_PUBLIC_KEY=settings.LANGFUSE_PUBLIC_KEY,
            LANGFUSE_HOST=settings.LANGFUSE_HOST
        )

    @staticmethod
    def get_llm(config: Config = None) -> ChatOpenAI:
        if not config:
            config = WorkflowFactory.get_config()
            
        return ChatOpenAI(
            model=config.llm_model,
            temperature=config.temperature,
            api_key=config.openai_api_key.get_secret_value()
        )

    @staticmethod
    def get_data_adapter(config: Config = None) -> SqliteSragAdapter:
        if not config:
            config = WorkflowFactory.get_config()
            
        return SqliteSragAdapter(
            db_uri=config.db_uri,
            root_dir=config.project_root
        )