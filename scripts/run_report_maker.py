import sys
import os
import json
from utils import set_path_to_imports
root_dir = set_path_to_imports()

try:
    from workflows.factory import WorkflowFactory
    # from workflows.srag_parallel_workflow import SragWorkflow
    # from workflows.srag_linear_workflow import SragWorkflow
    from workflows.srag_conditional_workflow import SragWorkflow
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running this script from the 'scripts' directory.")
    sys.exit(1)

def main(user_prompt):
    print("\n" + "="*60)
    print("EXECUTING END-TO-END SARS REPORT PIPELINE")
    print("="*60)
    
    # 1. Bootstrap Configuration
    # The Factory handles loading environment variables and settings
    try:
        config = WorkflowFactory.get_config()
    except Exception as e:
        print(f"Configuration Error: {e}")
        return

    # 2. Initialize the Orchestrator
    # SragWorkflow handles LLM init, Tool init, and Node wiring internally
    print("Initializing Workflow Orchestrator...")
    workflow_engine = SragWorkflow(config)

    # 3. Execute
    try:
        # The .run() method manages data loading and graph invocation
        result = workflow_engine.run(user_prompt)
        
        # 4. Extract Outputs
        final_path = result.get("final_report_path")
        metrics = result.get("metrics", {})
        synthesis = result.get("synthesis_result", {})
        
        print("\n" + "="*60)
        print("EXECUTION SUCCESSFUL")
        print("="*60)
        
        if final_path and "Error" not in final_path:
            print(f"Report Saved To:\n   -> {final_path}")
        else:
            print(f"Report Generation Issue: {final_path}")
            
        print("\n[Metric Summary]:")
        print(json.dumps(metrics, indent=2))
        
        print("\n[Executive Summary]:")
        print(synthesis.get("executive_summary", "N/A"))
        
    except Exception as e:
        print(f"\nPipeline Execution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    user_prompt = "Create a full report"
    # user_prompt = "Create a report with only metrics and charts"
    # user_prompt = "Create a report with only news"
    main(user_prompt)