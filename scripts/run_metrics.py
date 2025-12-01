import os
import sys
import sqlite3
import pandas as pd
from langchain_openai import ChatOpenAI
from utils import set_path_to_imports
root_dir = set_path_to_imports()
import sys

try:
    from workflows.agents.metric_analyst_llm.node import MetricsAnalystNode
    # from workflows.agents.metric_analyst_programmatic.node import MetricsAnalystNode
    from internal.data_retrieval.adapters.sqlite_loader import SqliteSragAdapter
    from workflows.agents.metric_analyst_llm.config import MetricConfig
    from workflows.metrics_workflow import MetricAnalystWorkflow
    from settings import settings
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running this script from the project root.")
    sys.exit(1)


def main():
    # 1. Create Configuration Object
    # We map the raw settings (env vars) to our strict Workflow Config
    try:
        config = MetricConfig(
            openai_api_key=settings.OPENAI_API_KEY,
            db_uri=settings.DB_URI,
            project_root=root_dir,
            llm_model="gpt-4o"
        )
    except Exception as e:
        print(f"Configuration Error: {e}")
        return

    import json

    # 2. Initialize Workflow
    # The workflow class handles setting up Adapters and LLMs internally
    print("Initializing Workflow...")
    workflow_engine = MetricAnalystWorkflow(config)

    # 5. Execute Node Logic
    try:
        print("\n" + "="*50 + "\nEXECUTING METRICS ANALYST (SQL AGENT)\n" + "="*50)
        result = workflow_engine.run()
        print("\n" + "="*50 + "\nRESULT METRICS\n" + "="*50)
        metrics = result.get("metrics", {})
        print(json.dumps(metrics, indent=2))
    except Exception as e:
        print(f"Execution Failed: {e}")

if __name__ == "__main__":
    main()