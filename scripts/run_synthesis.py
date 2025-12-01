import os
import sys
import json
from langchain_openai import ChatOpenAI
from utils import set_path_to_imports
root_dir = set_path_to_imports()

try:
    from settings import settings
    from workflows.workflow_config import MetricConfig
    from internal.data_retrieval.adapters.sqlite_loader import SqliteSragAdapter
    
    # Nodes (The Workers)
    from workflows.agents.metric_analyst_llm.node import MetricsAnalystNode
    from workflows.agents.chart_calculator.node import ChartCalculatorNode
    from workflows.agents.news_researcher.node import NewsResearcherNode
    
    # The Workflow to Test
    from workflows.synthesis_workflow import SynthesisWorkflow

except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def main():
    # 1. Configure
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

    # 2. Mock Upstream Data
    # mock_state = {
    #     "metrics": {
    #         "mortality_rate": 14.2,
    #         "icu_rate": 78.5,
    #         "increase_rate": 22.0
    #     },
    #     "news_snippets": [
    #         {"title": "New Variant Alert", "content": "Health ministry confirms community transmission of new strain."},
    #         {"title": "ICU Beds Full", "content": "Major hospitals in the metro area report 95% occupancy."}
    #     ],
    #     "chart_data": {
    #         "daily_cases_30d": [
    #             {"date": "2024-01-01", "count": 50}, 
    #             {"date": "2024-01-30", "count": 200}
    #         ]
    #     }
    # }

    # 2. Shared Infrastructure
    llm = ChatOpenAI(
        model=config.llm_model, 
        temperature=0, 
        api_key=config.openai_api_key.get_secret_value()
    )

    # 3. Load Data (Once for all agents)
    print("Loading SQLite Data...")
    try:
        adapter = SqliteSragAdapter(db_uri=config.db_uri, root_dir=config.project_root)
        df = adapter.get_raw_srag_data()
        print(f"Data Loaded: {len(df)} rows.")
    except Exception as e:
        print(f"Critical Data Load Error: {e}")
        return


    # 4. Execute Upstream Agents (Map Phase)
    # We manually execute the nodes here to build the state for the synthesis agent.
    
    # A. Metrics
    print("\n[1/3] Running Metrics Analyst...")
    metrics_node = MetricsAnalystNode(llm)
    metrics_result = metrics_node.execute({"raw_data": df, "include_metrics": True, "include_charts": False})
    metrics_data = metrics_result.get("metrics", {})

    # B. Charts (Data Calculation)
    print("\n[2/3] Running Chart Calculator...")
    chart_node = ChartCalculatorNode(llm)
    chart_result = chart_node.execute({"raw_data": df, "include_charts": True})
    chart_data = chart_result.get("chart_data", {})

    # C. News
    print("\n[3/3] Running News Researcher...")
    news_node = NewsResearcherNode(llm)
    # Note: News agent handles its own search query generation internally
    news_result = news_node.execute({}) 
    news_data = news_result.get("news_snippets", [])

    real_state = {
        "metrics": metrics_data,
        "chart_data": chart_data,
        "news_snippets": news_data
    }

    print("\n" + "="*50)
    print("EXECUTING SYNTHESIS AGENT")
    print("="*50)
    
    workflow = SynthesisWorkflow(config)
    result = workflow.run(real_state) # mock_state
    
    synthesis = result.get("synthesis_result", {})
    
    print("\n[EXECUTIVE SUMMARY]:")
    print(synthesis.get("executive_summary"))
    
    print("\n[RISK ASSESSMENT]:")
    print(synthesis.get("risk_assessment"))
    
    print("\n[DEEP DIVE]:")
    print(synthesis.get("deep_dive"))

if __name__ == "__main__":
    main()