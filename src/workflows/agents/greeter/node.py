# src/workflows/agents/greeter/node.py

import pandas as pd
from nodes.base import BaseNode

class GreeterNode(BaseNode):
    def __init__(self):
        super().__init__(llm=None, name="GreeterAgent")

    def execute(self, state: dict) -> dict:
        print(f"{'#'*40}")
        print(f"{' '*10} Hello {state['user_name']}!")
        print(f"{'#'*40}")
        return {"some_message": 'hello world string'}
