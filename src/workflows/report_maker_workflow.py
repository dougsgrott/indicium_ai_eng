import os
from langgraph.graph import StateGraph, END

# Import Domain Components
from .agents.report_maker.node import ReportMakerNode
from .agents.report_maker.states import ReportMakerState
from .workflow_config import MetricConfig

# Import Tool Factory
from tools.report_tool import setup_report_tool

class ReportMakerWorkflow:
    name = "ReportMaker"
    description = "Assembles final HTML report from analysis artifacts"

    def __init__(self, config: MetricConfig):
        self.config = config
        
        # 1. Initialize Report Tool
        # We rely on relative paths from the project root in settings
        template_dir = os.path.join(config.project_root, "reports", "templates")
        output_dir = os.path.join(config.project_root, "reports", "generated")
        
        self.tool = setup_report_tool(template_dir, output_dir)
        
        # 2. Initialize Node
        self.node = ReportMakerNode(self.tool)

    def _construct_graph(self):
        workflow = StateGraph(ReportMakerState)
        workflow.add_node("assembler", self.node.execute)
        workflow.set_entry_point("assembler")
        workflow.add_edge("assembler", END)
        return workflow.compile()

    def run(self, state: dict):
        app = self._construct_graph()
        return app.invoke(state)