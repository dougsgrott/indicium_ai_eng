from abc import ABC, abstractmethod


class BaseWorkflow(ABC):
    def __init__(self,):
        pass

    @abstractmethod
    def _construct_graph(self):
        pass

    def build(self,):
        graph = self._construct_graph()
        return graph.compile()