# plot_tool.py

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import logging
from langchain_core.tools import tool
from datetime import timedelta
from functools import wraps
from pathlib import Path

logger = logging.getLogger(__name__)

def setup_visualization_tool(db_uri: str, img_dir: str):
    """
    Factory function to initialize and configure the visualization tool.
    This separates configuration logic from the tool's execution logic.
    """
    try:
        os.makedirs(img_dir, exist_ok=True)
    except OSError as e:
        logger.critical(f"Failed to create image directory {img_dir}: {e}")
        raise

    class SarsChartGenerator:
        def __init__(self, db_uri: str, img_dir: str):
            self.db_uri = db_uri
            self.img_dir = img_dir

        def _get_data_for_plot(self, time_period: str) -> pd.Series | None:
            """Internal helper to query the DB and prepare time-series data."""
            # ... (Implementation of _get_data_for_plot remains the same) ...
            try:
                with sqlite3.connect(self.db_uri) as conn:
                    query = "SELECT DT_NOTIFIC FROM srag_records"
                    df = pd.read_sql_query(query, conn)
                
                df['DT_NOTIFIC'] = pd.to_datetime(df['DT_NOTIFIC'], errors='coerce')
                df = df.dropna(subset=['DT_NOTIFIC'])

                if df.empty:
                    logger.warning("Database query returned no valid date data.")
                    return pd.Series(dtype='int64')

                max_date = df['DT_NOTIFIC'].max()
                
                if time_period == 'daily_30d':
                    start_date = max_date - timedelta(days=30)
                    filtered = df[df['DT_NOTIFIC'] >= start_date]
                    counts = filtered.groupby('DT_NOTIFIC').size()
                    return counts.reindex(pd.date_range(start_date, max_date, freq='D'), fill_value=0)
                    
                elif time_period == 'monthly_12m':
                    start_date = max_date - timedelta(days=365)
                    filtered = df[df['DT_NOTIFIC'] >= start_date]
                    counts = filtered.groupby(pd.Grouper(key='DT_NOTIFIC', freq='M')).size()
                    return counts
                else:
                    raise ValueError(f"Invalid time period: {time_period}")

            except sqlite3.Error as e:
                logger.error(f"SQLite error during data fetching: {e}")
                return None
            except Exception as e:
                logger.error(f"General error in _get_data_for_plot: {e}")
                return None

        # 1. REMOVE @tool HERE! This is now a regular instance method.
        def generate_sars_charts(self, chart_type: str) -> str:
            """
            Generates required visualization charts and saves them as image files.
            
            Input `chart_type` must be one of the following:
            - 'daily_30d': For the daily case count over the last 30 days.
            - 'monthly_12m': For the monthly case count over the last 12 months.
            
            Returns the file path of the generated chart.
            """
            chart_config = {
                'daily_30d': {'title': 'Daily SARS Cases (Last 30 Days)', 'plot_type': 'bar', 'color': '#2E86C1'},
                'monthly_12m': {'title': 'Monthly SARS Cases (Last 12 Months)', 'plot_type': 'line', 'color': '#C0392B'},
            }
            
            if chart_type not in chart_config:
                logger.warning(f"Agent requested invalid chart_type: {chart_type}")
                return f"Error: Invalid chart_type '{chart_type}'. Must be 'daily_30d' or 'monthly_12m'."
            
            config = chart_config[chart_type]
            data_series = self._get_data_for_plot(chart_type)

            if data_series is None or data_series.empty:
                logger.error(f"Chart generation failed: No data for {config['title']}.")
                return f"Could not generate chart. Data is missing or failed to load for {config['title']}."

            try:
                # Plotting Logic (remains the same)
                plt.figure(figsize=(10, 6))
                
                if config['plot_type'] == 'bar':
                    data_series.plot(kind='bar', color=config['color'])
                    plt.xticks(rotation=45, ha='right', fontsize=8)
                elif config['plot_type'] == 'line':
                    data_series.plot(kind='line', marker='o', color=config['color'], linewidth=2)
                    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
                    plt.xticks(rotation=45, ha='right')

                plt.title(config['title'], fontsize=14, weight='bold')
                plt.xlabel('Date / Month', fontsize=12)
                plt.ylabel('Case Count', fontsize=12)
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.tight_layout()
                
                filename = os.path.join(self.img_dir, f"{chart_type}.png")
                plt.savefig(filename)
                plt.close()
                
                logger.info(f"Chart successfully saved to {filename}")
                return f"Success: Chart saved to {filename}"
            
            except Exception as e:
                logger.exception("Critical error during plotting execution.")
                return f"Critical error during plotting: {e}"

    # --- Tool Construction ---
    # 2. Instantiate the generator class
    generator = SarsChartGenerator(db_uri, img_dir)

    # 3. Create the external, decorated function
    # @wraps ensures the resulting function retains the docstring/metadata from generator.generate_sars_charts
    @wraps(generator.generate_sars_charts)
    @tool
    def generate_sars_charts(chart_type: str) -> str:
        """
        Generates required visualization charts and saves them as image files.
        
        Input `chart_type` must be one of the following:
        - 'daily_30d': For the daily case count over the last 30 days.
        - 'monthly_12m': For the monthly case count over the last 12 months.
        
        Returns the file path of the generated chart.
        """
        # Call the bound method on the instantiated generator object
        return generator.generate_sars_charts(chart_type)

    # 4. Return the new, decorated function
    return generate_sars_charts

# ----------------------------------------------------------------------
# 🎯 DEBUGGING BLOCK: Allows tool to be run independently for testing.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Setup Logging for local execution
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 2. Configuration (MOCK VALUES)
    # NOTE: Adjust these paths to point to your actual database and desired output folder.
    # The database path should include the prefix 'sqlite:///' if you use a full URI.
    DB_FILE = os.getenv("SARS_DB_URI", "./data/INFLUD19-26-06-2025.db")
    
    # Use a temporary folder for output, relative to the script location
    OUTPUT_FOLDER = Path("./test_charts").resolve()
    
    # 3. Initialize the Tool
    try:
        plot_tool = setup_visualization_tool(DB_FILE, str(OUTPUT_FOLDER))
        
        # Ensure the output directory exists
        os.makedirs(OUTPUT_FOLDER, exist_ok=True)
        
        print(f"\n--- Running Plot Tool Debug Test ---")
        print(f"Database URI assumed: {DB_FILE}")
        print(f"Output folder set to: {OUTPUT_FOLDER}")
        
        # 4. Test Queries (Invoke the tool directly)
        
        # Test 1: Daily Chart
        test_query_daily = "daily_30d"
        print(f"\nTesting: {test_query_daily}")
        result_daily = plot_tool.invoke(test_query_daily)
        print(f"Result: {result_daily}")
        
        # Test 2: Monthly Chart
        # test_query_monthly = "monthly_12m"
        # print(f"\nTesting: {test_query_monthly}")
        # result_monthly = plot_tool.invoke(test_query_monthly)
        # print(f"Result: {result_monthly}")
        
        print("\n--- Test Finished ---")
        
    except Exception as e:
        print(f"Error: {e}")