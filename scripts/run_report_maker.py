import os
import sys
import json
from langchain_openai import ChatOpenAI
from utils import set_path_to_imports
root_dir = set_path_to_imports()


try:
    from settings import settings
    from workflows.workflow_config import MetricConfig
    from workflows.report_maker_workflow import ReportMakerWorkflow

    # Infrastructure
    from internal.data_retrieval.adapters.sqlite_loader import SqliteSragAdapter
    from tools.report_tool import setup_report_tool
    
    # Nodes (The Agents)
    from workflows.agents.metric_analyst_llm.node import MetricsAnalystNode
    from workflows.agents.chart_calculator.node import ChartCalculatorNode
    from workflows.agents.chart_designer.node import ChartDesignerNode
    from workflows.agents.news_researcher.node import NewsResearcherNode
    from workflows.agents.synthesis_agent.node import SynthesisNode
    from workflows.agents.report_maker.node import ReportMakerNode
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

    # 2. Mock Completed State (Simulating full pipeline completion)
    # mock_state = {
    #     "metrics": {
    #         "mortality_rate": 12.5,
    #         "icu_rate": 45.2,
    #         "vaccination_rate": 60.0,
    #         "increase_rate": 5.5
    #     },
    #     "charts_html": {
    #         "daily_30d_html": "<div style='color:blue'>[Mock Daily Chart HTML]</div>",
    #         "monthly_12m_html": "<div style='color:red'>[Mock Monthly Chart HTML]</div>"
    #     },
    #     "news_snippets": [
    #         {"title": "Vaccination Campaign Success", "content": "Ministry reports 90% coverage in target groups.", "url": "http://news.com/vax"},
    #         {"title": "ICU Stability", "content": "Hospital occupancy remains stable.", "url": "http://news.com/icu"}
    #     ],
    #     "synthesis_result": {
    #         "executive_summary": "The situation is stable with a slight increase in cases but managed mortality.",
    #         "deep_dive": "Analysis shows that while cases rose by 5.5%, high vaccination rates (60%) are keeping ICU admissions low. The charts indicate a plateau.",
    #         "risk_assessment": "Moderate Risk. Continued monitoring recommended."
    #     }
    # }

    llm = ChatOpenAI(
        model=config.llm_model, 
        temperature=0, 
        api_key=config.openai_api_key.get_secret_value()
    )
    
    # Initialize Report Tool for the Assembler
    template_dir = os.path.join(config.project_root, "reports", "templates")
    output_dir = os.path.join(config.project_root, "reports", "generated")
    report_tool = setup_report_tool(template_dir, output_dir)

    # 3. Load Data
    print("\n[0/6] Loading Clinical Data...")
    try:
        adapter = SqliteSragAdapter(db_uri=config.db_uri, root_dir=config.project_root)
        df = adapter.get_raw_srag_data()
        print(f"   Success: Loaded {len(df)} rows.")
    except Exception as e:
        print(f"   Critical Error: {e}")
        return

    # --- EXECUTION PHASE (MAP) ---
    
    # 4. Metrics Analyst
    print("\n[1/6] Running Metrics Analyst (SQL Agent)...")
    metrics_node = MetricsAnalystNode(llm)
    metrics_res = metrics_node.execute({
        "raw_data": df, 
        "include_metrics": True, 
        "include_charts": False
    })
    metrics_data = metrics_res.get("metrics", {})

    # 5. Chart Data Calculator
    print("\n[2/6] Running Chart Calculator (SQL Agent)...")
    calc_node = ChartCalculatorNode(llm)
    calc_res = calc_node.execute({
        "raw_data": df, 
        "include_charts": True
    })
    chart_data = calc_res.get("chart_data", {})

    # 6. Chart Designer (Visuals)
    print("\n[3/6] Running Chart Designer (Plotly)...")
    design_node = ChartDesignerNode(llm)
    design_res = design_node.execute({"chart_data": chart_data})
    charts_html = design_res.get("charts_html", {})

    # 7. News Researcher
    print("\n[4/6] Running News Researcher (Web Search)...")
    news_node = NewsResearcherNode(llm)
    news_res = news_node.execute({}) # Node generates query internally
    news_data = news_res.get("news_snippets", [])

    # --- EXECUTION PHASE (REDUCE) ---

    # 8. Synthesis Agent
    print("\n[5/6] Running Synthesis Agent (Contextual Analysis)...")
    # Synthesis needs Metrics, News, and Charts (data summary)
    synthesis_state = {
        "metrics": metrics_data,
        "news_snippets": news_data,
        "chart_data": chart_data
    }
    synth_node = SynthesisNode(llm)
    synth_res = synth_node.execute(synthesis_state)
    synthesis_result = synth_res.get("synthesis_result", {})

    # 9. Report Maker (Assembler)
    print("\n[6/6] Running Report Maker (Assembly & Rendering)...")
    # Assembler needs everything
    final_state = {
        "metrics": metrics_data,
        "charts_html": charts_html,
        "news_snippets": news_data,
        "synthesis_result": synthesis_result
    }
    
    maker_node = ReportMakerNode(report_tool)
    maker_res = maker_node.execute(final_state)
    final_path = maker_res.get("final_report_path")


    # print("\n" + "="*50)
    # print("EXECUTING REPORT MAKER")
    # print("="*50)
    
    # workflow = ReportMakerWorkflow(config)
    # result = workflow.run(mock_state)

    # final_path = result.get("final_report_path")
    # print(f"\nFinal Report Path: {final_path}")
    
    # --- CONCLUSION ---
    print("\n" + "="*60)
    print("✅ PIPELINE COMPLETE")
    print("="*60)

    if final_path and os.path.exists(final_path):
        print("Success: File exists on disk.")
    else:
        print("Error: File was not created.")

if __name__ == "__main__":
    main()