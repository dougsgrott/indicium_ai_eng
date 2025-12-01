import os
import sys
import json
from utils import set_path_to_imports
root_dir = set_path_to_imports()


try:
    from settings import settings
    from workflows.workflow_config import MetricConfig
    from workflows.chart_pipeline_workflow import ChartPipelineWorkflow
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

    # 2. Initialize Pipeline
    print("Initializing Chart Pipeline...")
    pipeline = ChartPipelineWorkflow(config)

    # 3. Execute
    print("\n" + "="*50)
    print("EXECUTING PIPELINE (Calculator -> Designer)")
    print("="*50)
    
    try:
        result = pipeline.run()
        
        if not result:
            print("Pipeline returned no result.")
            return

        # 4. Process Results
        chart_data = result.get("chart_data", {})
        html_outputs = result.get("charts_html", {})
        
        print("\n" + "="*50)
        print("PIPELINE RESULTS")
        print("="*50)
        
        # Verify Data
        daily_pts = len(chart_data.get('daily_cases_30d', []))
        monthly_pts = len(chart_data.get('monthly_cases_12m', []))
        print(f"1. Data Extraction: Success")
        print(f"   - Daily Points: {daily_pts}")
        print(f"   - Monthly Points: {monthly_pts}")
        
        # Verify Visuals
        print(f"2. Visualization: {len(html_outputs)} charts generated")
        
        # Save Outputs
        output_dir = os.path.join(root_dir, "reports", "images")
        os.makedirs(output_dir, exist_ok=True)
        
        for name, html_content in html_outputs.items():
            file_path = os.path.join(output_dir, f"{name}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"   - Saved: {file_path}")

    except Exception as e:
        print(f"Pipeline Execution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()