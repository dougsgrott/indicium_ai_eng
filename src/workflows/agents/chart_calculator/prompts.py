# src/workflows/agents/chart_calculator/prompts.py

SYSTEM_PROMPT = """
You are an expert SQL Data Analyst specialized in Time-Series Data.
You are analyzing the Brazilian SRAG database to extract data points for visualizations.
"""

REFERENCE_DATE_CONTEXT = """
**TEMPORAL CONTEXT:**
- **Reference Date ("Today"):** {reference_date}
- **30-Day Window:** {date_30d_ago} to {reference_date}
- **12-Month Window:** {date_12m_ago} to {reference_date}
"""

REQUEST_CHARTS = """
Retrieve the data points required for charts:
1. "daily_cases_30d": List of daily case counts for the "LAST 30 DAYS" window. 
   - GROUP BY day.
   - Keys MUST be: "date" (YYYY-MM-DD), "count" (Int).
2. "monthly_cases_12m": List of monthly case counts for the "LAST 12 MONTHS" window.
   - GROUP BY month.
   - Keys MUST be: "date" (YYYY-MM-DD), "count" (Int).
"""

CHART_CALCULATION_PROMPT = """
{data_dictionary}

{reference_context}

**YOUR TASK:**
{request}

**CRITICAL OUTPUT INSTRUCTIONS:**
1. **Execute SQL:** Generate and run the necessary SQL queries.
2. **JSON Only:** Return the final answer ONLY as a valid JSON object. No markdown.
3. **Naming:** Use descriptive snake_case keys (e.g., "daily_cases_30d").
4. **Data Types:** List of Objects (e.g., `[{{"date": "2024-01-01", "count": 10}}, ...]`).
"""