# plot_tool.py

import os
import sqlite3
import pandas as pd
import logging
import plotly.express as px
from langchain_core.tools import tool
from datetime import timedelta
from functools import wraps
from pathlib import Path

logger = logging.getLogger(__name__)

def _normalize_sqlite_uri(uri: str) -> str:
    # Handles sqlite:///absolute/path.db
    if uri.startswith("sqlite:///"):
        return uri.replace("sqlite:///", "", 1)

    # Handles sqlite://relative/path.db
    if uri.startswith("sqlite://"):
        return uri.replace("sqlite://", "", 1)

    return uri


def setup_visualization_tool(db_uri: str, img_dir: str):
    # Extract file path from URI (remove sqlite:///)
    db_path = db_uri.replace("sqlite:///", "")

    def _get_data(period: str) -> pd.DataFrame:
        try:
            norm_db_path = _normalize_sqlite_uri(db_path)
            conn = sqlite3.connect(norm_db_path)
            # SQLite specific: strftime to normalize dates
            query = "SELECT DT_NOTIFIC FROM srag_records WHERE DT_NOTIFIC IS NOT NULL"
            df = pd.read_sql_query(query, conn)
            conn.close()

            # Convert to datetime
            df['DT_NOTIFIC'] = pd.to_datetime(df['DT_NOTIFIC'], format='%Y-%m-%d')
            df = df.dropna()
            
            if df.empty: return pd.DataFrame()

            max_date = df['DT_NOTIFIC'].max()
            
            if period == 'daily_30d':
                start_date = max_date - timedelta(days=30)
                filtered = df[df['DT_NOTIFIC'] >= start_date]
                # Count by day
                counts = filtered.groupby('DT_NOTIFIC').size().reset_index(name='Cases')
            else: # monthly_12m
                start_date = max_date - timedelta(days=365)
                filtered = df[df['DT_NOTIFIC'] >= start_date]
                # Group by Month
                counts = filtered.groupby(pd.Grouper(key='DT_NOTIFIC', freq='M')).size().reset_index(name='Cases')
                
            return counts
        except Exception as e:
            logger.error(f"Data fetch error: {e}")
            return pd.DataFrame()

    @tool
    def generate_chart(chart_type: str) -> str:
        """Generates 'daily_30d' or 'monthly_12m' charts."""
        df = _get_data(chart_type)
        if df.empty: return "Error: No Data"
        
        if chart_type == 'daily_30d':
            title = "Daily Cases (30 Days)"
            fig = px.bar(df, x='DT_NOTIFIC', y='Cases', title=title)
        else:
            title = "Monthly Cases (12 Months)"
            fig = px.line(df, x='DT_NOTIFIC', y='Cases', title=title, markers=True)
        
        filename = f"{img_dir}/{chart_type}.html"
        fig.write_html(filename, include_plotlyjs='cdn', full_html=False)
        return f"Success: Chart saved to {filename}"

    return generate_chart











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
