# import os
# import sys
# import json
# from utils import set_path_to_imports
# root_dir = set_path_to_imports()

# try:
#     from workflows.chart_designer_workflow import ChartPipelineWorkflow
# except ImportError as e:
#     print(f"Import Error: {e}")
#     sys.exit(1)

# def main():
#     # 1. Mock Data (Simulating output from Chart Calculator)
#     # This represents the sparse data already filled by the previous agent
#     mock_input = {
#         "chart_data": {
#             "daily_cases_30d": [
#                 {"date": "2024-01-01", "count": 10},
#                 {"date": "2024-01-02", "count": 15},
#                 {"date": "2024-01-03", "count": 8},
#                 {"date": "2024-01-04", "count": 20},
#                 {"date": "2024-01-05", "count": 25},
#             ],
#             "monthly_cases_12m": [
#                 {"date": "2023-01", "count": 120},
#                 {"date": "2023-02", "count": 150},
#                 {"date": "2023-03", "count": 300},
#                 {"date": "2023-04", "count": 100},
#             ]
#         }
#     }

#     # 2. Initialize Workflow
#     print("Initializing Chart Designer Workflow...")
#     designer = ChartPipelineWorkflow()

#     # 3. Execute
#     print("\n" + "="*50)
#     print("GENERATING CHARTS")
#     print("="*50)
    
#     try:
#         result = designer.run(mock_input)
        
#         charts = result.get("charts_html", {})
        
#         # 4. Verify Output
#         for name, html in charts.items():
#             print(f"\n--- {name} ---")
#             print(f"Status: Generated ({len(html)} chars)")
#             print(f"Snippet: {html[:150]}...")
            
#             # # Optional: Save to inspect visually
#             # output_path = os.path.join(current_dir, f"test_{name}.html")
#             # with open(output_path, "w") as f:
#             #     f.write(html)
#             # print(f"Saved preview to: {output_path}")

#     except Exception as e:
#         print(f"Workflow Execution Failed: {e}")
#         import traceback
#         traceback.print_exc()

# if __name__ == "__main__":
#     main()