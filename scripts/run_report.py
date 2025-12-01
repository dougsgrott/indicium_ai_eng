# run_report.py
import os
import pandas as pd
from langchain_openai import ChatOpenAI  # Or your preferred LLM provider
from workflows.srag_workflow import build_workflow
# from src.internal.data_retrieval.adapters.csv.datasus_loader import DatasusCsvAdapter

# 1. Configuration
CSV_PATH = "path/to/your/INFLUD21.csv"  # Replace with your actual CSV path
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Ensure API key is set

# 2. Initialize Infrastructure
# Initialize the LLM (this will be passed to the nodes)
llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=OPENAI_API_KEY)

# Initialize Data Adapter and Load Data
print("Loading data from CSV...")
# data_adapter = DatasusCsvAdapter(csv_path=CSV_PATH)
# raw_df = data_adapter.get_raw_srag_data()
# print(f"Data loaded. Shape: {raw_df.shape}")

# 3. Build the Graph
# We need to modify the workflow builder to accept the LLM instance
# You might need to update `build_workflow` signature in `srag_workflow.py` 
# to accept `llm` and pass it to the Node classes.
workflow_app = build_workflow() #llm 

# 4. Define Initial State
initial_state = {
    "raw_data": pd.DataFrame(), #raw_df,
    "metrics": {},
    "news_analysis": "",
    "charts": [],
    "final_report": ""
}

# 5. Execute the Workflow
print("Starting workflow execution...")
# .invoke() runs the graph synchronously
final_state = workflow_app.invoke(initial_state)

# 6. Retrieve Output
report = final_state.get("final_report")
charts = final_state.get("charts")

print("\n" + "="*50)
print("FINAL REPORT GENERATED")
print("="*50)
print(report)

# Optional: Save Charts
if charts:
    print(f"\n[System]: Saving {len(charts)} charts locally...")
    for i, img_data in enumerate(charts):
        with open(f"chart_{i}.png", "wb") as f:
            import base64
            f.write(base64.b64decode(img_data))
    print("Charts saved.")