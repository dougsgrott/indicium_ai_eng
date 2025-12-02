# src/workflows/workflow_states.py

from typing import TypedDict, Dict, Any, List, Annotated
import operator
from src.workflows.agents.chart_designer.states import ChartDesignerState
from src.workflows.agents.chart_calculator.states import ChartCalculatorState
from src.workflows.agents.metric_analyst.states import Metrics
from src.workflows.agents.news_researcher.states import NewsResearcherState
from src.workflows.agents.synthesis_agent.states import SynthesisAgentState

class SragWorkflowState(TypedDict):
    # Initial Input
    user_prompt: str
    raw_data: Any

    include_metrics: bool
    include_charts: bool
    include_news: bool

    # Intermediate Artifacts
    metrics_state: Metrics
    chart_calc_state: ChartCalculatorState
    chart_plot_state: ChartDesignerState
    news_state: NewsResearcherState
    synthesis_state: SynthesisAgentState
    
    # Final Output
    final_report_path: str

    # --- SYNCHRONIZATION MECHANISM ---
    branches_completed: Annotated[List[str], operator.add]
    expected_count: int
