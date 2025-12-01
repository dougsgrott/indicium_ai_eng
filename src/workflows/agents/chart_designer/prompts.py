SYSTEM_PROMPT = """
You are a Data Visualization Expert specializing in Plotly.js.
Your job is to generate robust, responsive HTML snippets for charts.
"""

CHART_GENERATION_PROMPT = """
Generate a **standalone HTML snippet** containing a `<div>` and a `<script>` tag to render a Plotly chart based on the data below.

### CONFIGURATION
- **Chart Title:** {title}
- **Chart Type:** {chart_type} (e.g. 'bar' or 'line')
- **Target Div ID:** `{div_id}` (You MUST use this exact ID)
- **Primary Color:** {color}

### DATA
{data_json}

### REQUIREMENTS
1. **HTML Structure:**
   - Create a `<div>` with `id="{div_id}"` and `style="height:350px; width:100%;"`.
   - Create a `<script>` tag immediately after.
2. **JavaScript Logic:**
   - Use `Plotly.newPlot('{div_id}', data, layout, config)`.
   - **X-Axis:** extract from the data (look for keys like 'date', 'dt_notific', or 'period').
   - **Y-Axis:** extract from the data (look for keys like 'count', 'cases', 'value').
3. **Styling:**
   - Layout: `margin: {{l:40, r:20, t:40, b:40}}`, transparent background (`paper_bgcolor='rgba(0,0,0,0)'`).
   - Config: `responsive: true`, `displayModeBar: false`.
   - **CRITICAL:** `xaxis: {{ rangeslider: {{ visible: false }} }}` to prevent visual glitches.

**OUTPUT FORMAT:**
Return ONLY the HTML code (div + script). Do not include markdown fences (```html).
"""