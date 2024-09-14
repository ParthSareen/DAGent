import logging
from .DagNode import DagNode

class FunctionNode(DagNode):
    def __init__(self, func: callable, tool_description = dict | None, next_nodes: dict[str, DagNode] = None, user_params: dict | None = None):
        super().__init__(func, next_nodes)
        self.tool_description = tool_description
        self.user_params = user_params or {}
        self.compiled = False
        self.node_result = None
        self.logger = logging.getLogger(__name__)
    
    def compile(self, force_load=False) -> None:
        self.logger.info(f"Compiling FunctionNode for function: {self.func.__name__}")
        self.compiled = True
        if isinstance(self.next_nodes, list):
            self.logger.debug("Converting next_nodes from list to dictionary")
            self.next_nodes = {node.func.__name__: node for node in self.next_nodes}
        for node_name, next_node in self.next_nodes.items():
            self.logger.debug(f"Compiling next node: {node_name}")
            next_node.compile(force_load=force_load)

    def run(self, **kwargs) -> any:
        if not self.compiled:
            self.logger.error("Attempted to run uncompiled node")
            raise ValueError("Node not compiled. Please run compile() method from the entry node first")
        
        self.logger.info(f"Running FunctionNode for function: {self.func.__name__}")
        merged_params = {**self.user_params, **kwargs}    
        self.logger.debug(f"Merged parameters: {merged_params}")

        try:
            self.node_result = self.func(**merged_params)
            self.logger.debug(f"Function result: {self.node_result}")
        except Exception as e:
            self.logger.error(f"Error executing function {self.func.__name__}: {str(e)}")
            raise

        # Pass the result to the next nodes if any
        # TODO: figure out param logic pattern
        if not self.next_nodes:
            self.logger.info(f"No next nodes after {self.func.__name__}, returning result")
            return self.node_result
        for node_name, next_node in self.next_nodes.items():
            self.logger.info(f"Passing result to next node: {node_name}")
            # TODO: creating data models for passing info between nodes 
            params = {'prev_output': self.node_result, **next_node.user_params}
            self.logger.debug(f"Parameters for next node: {params}")
            next_node.run(**params)

def FuncNode(next_nodes: dict[str, 'DagNode'] | list['DagNode'] | None = None):
    def decorator(func):
        node = FunctionNode(func, next_nodes=next_nodes)
        return node
    return decorator
