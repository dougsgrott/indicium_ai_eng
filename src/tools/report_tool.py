# report_tool.py

import os
import logging
import json
from langchain_core.tools import tool
from jinja2 import Environment, FileSystemLoader, select_autoescape
from functools import wraps
import pandas as pd
import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

# --- Factory Function Setup ---

def setup_report_tool(template_dir: str, output_dir: str):
    """Initializes the ReportGenerator and returns the decorated tool function."""
    
    try:
        # Use absolute path for template directory to avoid relative path errors
        abs_template_dir = os.path.abspath(template_dir)
        file_loader = FileSystemLoader(abs_template_dir)
        
        env = Environment(
            loader=file_loader,
            autoescape=select_autoescape(['html', 'xml'])
        )
    except Exception as e:
        logger.critical(f"Failed to initialize Jinja2 loader for directory {template_dir}: {e}")
        raise

    class ReportGenerator:
        def __init__(self, output_dir: str):
            # Force absolute path for determinism
            self.output_dir = os.path.abspath(output_dir)
            os.makedirs(self.output_dir, exist_ok=True)
            print(f"[Report Tool] Initialized. Reports will be saved to: {self.output_dir}")

        def _generate_save_report(self, html_content):
            try:
                timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                filename = f"SARS_Report_{timestamp}.html"
                html_path = os.path.join(self.output_dir, filename)
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # Success message returned to the agent
                msg = f"Report successfully saved to: {html_path}"
                print(f"[Report Tool] {msg}")
                logger.info(msg)
                return msg

            except Exception as e:
                error_msg = f"Report generation failed: File Save Error. Error: {e}"
                logger.exception(error_msg)
                print(f"[Report Tool] ERROR: {error_msg}")
                return error_msg

        def _render_html(self, data: Dict[str, Any]) -> str:
            """Loads Jinja template and renders it with the collected data."""
            try:
                template = env.get_template('sars_report_template.html')
                data['current_date'] = datetime.date.today().strftime("%Y-%m-%d")
                html_output = template.render(**data)
                return html_output
            except Exception as e:
                logger.error(f"Failed to render Jinja template: {e}")
                raise

        def _parse_input(self, report_data_json):
            import json
            try:
                safe_json_string = report_data_json.replace('\\', '/')
                data_dict = json.loads(safe_json_string) 
            except json.JSONDecodeError as e:
                error_msg = f"Report generation failed: JSON Decoding Error. Input malformed. Error: {e}"
                logger.exception(error_msg)
                print(f"[Report Tool] ERROR: {error_msg}")
                data_dict = json.loads(report_data_json)
            except Exception as e:
                error_msg = f"Report generation failed: Unexpected error during JSON parsing. Error: {e}"
                logger.exception(error_msg)
                return error_msg
            return data_dict

        def _normalize_structure(self, data_dict):
            # Safely retrieve nested components, defaulting to empty structures
            commentary_data = data_dict.get('commentary', {})
            top_level_news = data_dict.get('news', [])

            final_data = {
                # Metrics: Safely retrieve metrics or default to empty dict
                'metrics': data_dict.get('metrics', {}),

                # Commentary: Build the mandatory top-level structure for Jinja
                'commentary': {
                    'summary': commentary_data.get('summary', 'The agent did not provide a synthesis. See snippets below.'),
                    # Combine news sources from potential locations (top level or nested)
                    'news_sources': top_level_news or commentary_data.get('news_sources', [])
                },

                # Charts & Date
                'charts': data_dict.get('charts', {}),
                'current_date': datetime.date.today().strftime("%Y-%m-%d"),

                'audit': data_dict.get('audit', {})
            }
            return final_data

        def generate_final_report(self, report_data_json: str) -> str:
            """
            Generates the final, structured report by combining metrics, news, and HTML plots.
            """
            
            print(f"[Report Tool] Processing request... (Input size: {len(report_data_json)} chars)")

            # --- STEP 1: PARSE INPUT (CRITICAL EXTERNAL I/O) ---
            data_dict = self._parse_input(report_data_json)

            # --- STEP 2: STRUCTURE NORMALIZATION (Internal Logic - No Try/Except Needed) ---            
            final_data = self._normalize_structure(data_dict)

            # --- STEP 3: RENDER HTML (CRITICAL EXTERNAL OPERATION) ---
            try:
                html_content = self._render_html(final_data) 
            except Exception as e:
                error_msg = f"Report generation failed: Jinja Rendering Error. Error: {e}"
                logger.exception(error_msg)
                print(f"[Report Tool] ERROR: {error_msg}")
                return error_msg

            # --- STEP 4: GENERATE FILENAME AND SAVE (CRITICAL EXTERNAL I/O) ---
            msg = self._generate_save_report(html_content)
            return msg


    # --- Tool Construction ---
    generator = ReportGenerator(output_dir)

    @wraps(generator.generate_final_report)
    @tool
    def generate_final_report(report_data_json: str) -> str:
        """
        MANDATORY: Use this tool to SAVE the final HTML report to the disk.
        
        DO NOT output the report HTML directly in the chat.
        DO NOT finish the task without calling this tool.

        Identity: You are the final report synthesizer.
        Input: You have the raw metrics (in one state key), news snippets (in another), and chart HTML content (in another)
        
        Input: A valid JSON string containing:
        {
            "metrics": { ... },
            "news": [ ... ],
            "charts": {
                "daily_30d_html": "<div id='...'> [REAL PLOT HTML from to_html()] </div>",
                "monthly_12m_html": "<div id='...'> [REAL PLOT HTML from to_html()] </div>"
            }
        }
        """

        return generator.generate_final_report(report_data_json)
    
    return generate_final_report

# ----------------------------------------------------------------------
# 🎯 DEBUGGING BLOCK: Test tool with metric data only.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    from pathlib import Path

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