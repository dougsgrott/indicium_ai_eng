import sys
import os
import json
from utils import set_path_to_imports

# Set up paths
root_dir = set_path_to_imports()

try:
    from workflows.factory import WorkflowFactory
    
    # Import ALL workflows, aliasing them to distinguish them
    from workflows.srag_linear_workflow import SragWorkflow as LinearWorkflow
    from workflows.srag_parallel_workflow import SragWorkflow as ParallelWorkflow
    from workflows.srag_conditional_workflow import SragWorkflow as ConditionalWorkflow

except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running this script from the 'scripts' directory.")
    sys.exit(1)

def get_user_selection():
    """
    Interactive menu to select workflow type and prompts.
    Returns: (WorkflowClass, user_prompt_string)
    """
    print("\nSelect Execution Mode:")
    print("1. Linear Workflow (Waterfall - Deterministic)")
    print("2. Parallel Workflow (Fan-Out/Fan-In - Deterministic)")
    print("3. Conditional Workflow (Intent-Based - User Input)")
    
    while True:
        choice = input("\nEnter choice [1-3]: ").strip()
        
        if choice == '1':
            print(">> Selected: Linear Workflow")
            # Linear usually runs a full report by default, prompt is metadata
            return LinearWorkflow, "Full Report (Linear Mode)"
            
        elif choice == '2':
            print(">> Selected: Parallel Workflow")
            # Parallel runs full report by default
            return ParallelWorkflow, "Full Report (Parallel Mode)"
            
        elif choice == '3':
            print(">> Selected: Conditional Workflow")
            user_input = input(">> Enter your request (e.g., 'Only show me news about vaccines'): ").strip()
            if not user_input:
                user_input = "Create a full report" # Default fallback
            return ConditionalWorkflow, user_input
            
        else:
            print("Invalid selection. Please try again.")

def safe_get(data: dict, key: str, default=None):
    """
    Helper to retrieve data from either Flat State or Namespaced State.
    This ensures the script works regardless of which state pattern the workflow uses.
    """
    # 1. Try Flat Access (Old Pattern)
    if key in data:
        return data[key]
    
    # 2. Try Namespaced Access (New Pattern)
    # Map common keys to their namespaces
    namespaces = {
        "metrics": "metrics_state",
        "chart_data": "chart_calc_state",
        "charts_html": "chart_plot_state",
        "news_snippets": "news_state",
        "synthesis_result": "synthesis_state"
    }
    
    if key in namespaces:
        ns = namespaces[key]
        if ns in data and isinstance(data[ns], dict):
            return data[ns].get(key, default)
            
    return default

def main():
    print("\n" + "="*60)
    print("EXECUTING END-TO-END SARS REPORT PIPELINE")
    print("="*60)

    # 1. Get User Intent
    WorkflowClass, user_prompt = get_user_selection()

    # 2. Bootstrap Configuration
    try:
        config = WorkflowFactory.get_config()
    except Exception as e:
        print(f"Configuration Error: {e}")
        return

    # 3. Initialize the Orchestrator
    print(f"\nInitializing {WorkflowClass.name}...")
    workflow_engine = WorkflowClass(config)

    # 4. Execute
    try:
        print(f"Running with prompt: '{user_prompt}'")
        # The .run() method manages data loading and graph invocation
        result = workflow_engine.run(user_prompt)
        
        # 5. Extract Outputs (Using robust helper)
        final_path = result.get("final_report_path")
        metrics = safe_get(result, "metrics", {})
        synthesis = safe_get(result, "synthesis_result", {})
        
        print("\n" + "="*60)
        print("EXECUTION SUCCESSFUL")
        print("="*60)
        
        if final_path and "Error" not in final_path:
            print(f"Report Saved To:\n   -> {final_path}")
        else:
            print(f"Report Generation Issue: {final_path}")
            
        print("\n[Metric Summary]:")
        # Handle case where metrics might be nested or empty
        print(json.dumps(metrics, indent=2, default=str))
        
        print("\n[Executive Summary]:")
        if isinstance(synthesis, dict):
            print(synthesis.get("executive_summary", "N/A"))
        else:
            print(str(synthesis))
        
    except Exception as e:
        print(f"\nPipeline Execution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()