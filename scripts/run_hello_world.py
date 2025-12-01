from utils import set_path_to_imports
import sys
set_path_to_imports()

try:
    from workflows.hello_world_workflow import GreeterWorkflow
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)


print("Running Hello World Workflow...")
workflow = GreeterWorkflow()
initial_state = {"user_name": "World"}

print("Starting workflow execution...\n")
llm = workflow.build()
llm.invoke(initial_state)
