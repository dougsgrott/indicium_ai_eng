# report_tool.py

import os
import logging
import json
from langchain_core.tools import tool
from jinja2 import Environment, FileSystemLoader, select_autoescape
from functools import wraps
import pandas as pd
import datetime
from typing import Dict, Any, Union, List
from pathlib import Path

logger = logging.getLogger(__name__)

# --- Factory Function Setup ---

def setup_report_tool(template_dir: str, output_dir: str):
    """Initializes the ReportGenerator and returns the decorated tool function."""
    
    try:
        # 1. Initialize Jinja Environment (Security Note: autoescape is good practice)
        file_loader = FileSystemLoader(template_dir)
        env = Environment(
            loader=file_loader,
            autoescape=select_autoescape(['html', 'xml'])
        )
    except Exception as e:
        logger.critical(f"Failed to initialize Jinja2 loader for directory {template_dir}: {e}")
        raise

    class ReportGenerator:
        def __init__(self, output_dir: str):
            self.output_dir = output_dir
            os.makedirs(self.output_dir, exist_ok=True)

        def _render_html(self, data: Dict[str, Any]) -> str:
            """Loads Jinja template and renders it with the collected data."""
            try:
                template = env.get_template('sars_report_template.html')
                
                # Add current date to the data dictionary
                data['current_date'] = datetime.date.today().strftime("%Y-%m-%d")
                
                # Render the template using the unpacked dictionary
                html_output = template.render(**data)
                return html_output
            except Exception as e:
                logger.error(f"Failed to render Jinja template: {e}")
                raise

        def generate_final_report(self, report_data_json: str) -> str:
            """
            Generates the final, structured report by combining all preceding data.
            """
            try:
                # 1. Parse Input & Sanitize
                safe_json_string = report_data_json.replace('\\', '/')
                data = json.loads(safe_json_string)

                # 2. 🎯 CRITICAL FIX: STRUCTURE REPAIR AND DEFAULTING
                
                # Define keys that are flat in the AI's output but belong in 'metrics':
                flat_metric_keys = ['mortality_rate', 'rate_of_increase', 'icu_occupancy', 'vaccination_rate', 'cases_last_week', 'cases_this_week']

                # Initialize the structured final data
                final_data = {}
                
                # --- A. Consolidate Metrics ---
                metrics_data = data.pop('metrics', {}) # Use existing 'metrics' if present
                for key in flat_metric_keys:
                    # Pull flat keys from the root data dictionary into 'metrics_data'
                    metrics_data[key] = data.pop(key, metrics_data.get(key, 'N/A'))
                final_data['metrics'] = metrics_data
                
                # --- B. Consolidate News/Commentary ---
                news_data = data.pop('news', [])
                commentary_data = data.pop('commentary', {})
                
                final_data['news'] = news_data
                final_data['commentary'] = {
                    # Provide a robust default summary if the AI skipped synthesis
                    'summary': commentary_data.get('summary', 'The agent did not provide a synthesis. See snippets below.'),
                    'news_sources': news_data # Can reuse the news data here if template needs it
                }
                
                # --- C. Consolidate Charts ---
                final_data['charts'] = data.pop('charts', [])
                
                # 3. Render HTML
                html_content = self._render_html(final_data)
                
                # 4. Generate Filename and Save
                timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                html_path = os.path.join(self.output_dir, f"SARS_Report_{timestamp}.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                     f.write(html_content)
                
                logger.info(f"Final Report successfully generated as HTML: {html_path}")
                return f"Success: Report generated and saved to {html_path}. (Ready for PDF conversion)"

            except Exception as e:
                logger.exception("Critical error during final report generation.")
                return f"Report generation failed: {e}"

    # --- Tool Construction ---
    generator = ReportGenerator(output_dir)

    @wraps(generator.generate_final_report)
    @tool
    def generate_final_report(report_data_json: str) -> str:
        """
        Generates the final, structured PDF report by combining all preceding data
        (metrics, news, and chart file paths) received as a JSON string.
        
        The input `report_data_json` MUST contain metrics, charts (optional list of paths), 
        and news/commentary (optional). Example keys: mortality_rate, charts, news.
        """
        return generator.generate_final_report(report_data_json)
    
    return generate_final_report


# ----------------------------------------------------------------------
# 🎯 DEBUGGING BLOCK: Test tool with metric data only.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Setup Logging and Configuration
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create necessary output directories locally for testing
    TEST_OUTPUT_DIR = Path("./reports/generated_reports").resolve()
    TEST_TEMPLATE_DIR = Path("./reports/templates").resolve()
    MOCK_DATA_DIR = Path("./data/mock_data").resolve()
    MOCK_DATA = {}

    with open(MOCK_DATA_DIR / 'metrics.json', 'r') as file:
        MOCK_METRICS_DATA = json.load(file)
        MOCK_DATA.update(MOCK_METRICS_DATA)

    with open(MOCK_DATA_DIR / 'news.json', 'r') as file:
        MOCK_NEWS_DATA = {"news": json.load(file)}
        MOCK_DATA.update(MOCK_NEWS_DATA)

    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEST_TEMPLATE_DIR, exist_ok=True)

    TEMPLATE_FILE_PATH = TEST_TEMPLATE_DIR / "sars_report_template.html"
    
    # The agent wraps the data into a JSON string
    TEST_JSON_INPUT = json.dumps(MOCK_DATA)

    # 4. Initialize and Run the Tool
    print("\n--- Running Report Tool Debug Test (Metric Data Only) ---")
    try:
        report_tool = setup_report_tool(str(TEST_TEMPLATE_DIR), str(TEST_OUTPUT_DIR))
        
        result = report_tool.invoke(TEST_JSON_INPUT)
        
        print(f"\nResult: {result}")
        print(f"File created successfully at: {TEST_OUTPUT_DIR}")

    except Exception as e:
        print(f"\n--- TEST FAILED ---")
        print(f"Error during report generation test: {e}")