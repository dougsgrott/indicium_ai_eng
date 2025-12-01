# src/workflows/run_chart_calc.py

import os
import sys
import json
from utils import set_path_to_imports
root_dir = set_path_to_imports()


try:
    from settings import settings
    from workflows.workflow_config import MetricConfig
    from workflows.chart_calc_workflow import ChartCalculatorWorkflow
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running this script from the 'src' directory.")
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

    # 2. Initialize
    print("Initializing Chart Calculator Workflow...")
    workflow_engine = ChartCalculatorWorkflow(config)

    # 3. Execute
    print("\n" + "="*50)
    print("STARTING CHART DATA CALCULATION")
    print("="*50)

    try:
        result = workflow_engine.run()
        
        print("\n" + "="*50)
        print("FINAL CHART DATA (Snippet)")
        print("="*50)
        
        data = result.get("chart_data", {})
        
        # Pretty print a summary to avoid flooding console with 365 days of data
        daily = data.get("daily_cases_30d", [])
        monthly = data.get("monthly_cases_12m", [])
        
        print(f"Daily Data Points: {len(daily)}")
        if daily:
            print(f"First 3: {json.dumps(daily[:3], indent=2)}")
            print("...")
            
        print(f"\nMonthly Data Points: {len(monthly)}")
        if monthly:
            print(f"All Months: {json.dumps(monthly, indent=2)}")
            
        if "error" in data:
            print(f"\nERROR: {data['error']}")
        
    except Exception as e:
        print(f"Workflow Execution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()