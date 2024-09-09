import json
import os
import inspect
from .DagNode import DagNode

from .base_functions import call_llm_tool, create_tool_desc
import logging


class DecisionNode(DagNode):
    def __init__(
        self, 
        func: callable = call_llm_tool, 
        next_nodes: dict[str, DagNode] = None,
        user_params: dict | None = None,
        model: str = 'gpt-4-0125-preview',
        api_base: str | None = None,
        tool_json_dir: str = 'Tool_JSON',
        retry_json_count: int = 3
    ):
        super().__init__(func, next_nodes)
        self.user_params = user_params or {}
        self.logger = logging.getLogger(__name__)
        self.compiled = False
        self.api_base = api_base
        self.model = model
        self.tool_json_dir = tool_json_dir
        self.retry_json_count = retry_json_count
    
    def compile(self, force_load=False) -> None:
        self.compiled = True

        if isinstance(self.next_nodes, list):
            self.next_nodes = {node.func.__name__: node for node in self.next_nodes}

        for _, next_node in self.next_nodes.items():
            func_name = os.path.join(self.tool_json_dir, next_node.func.__name__ + '.json')
            self.logger.info(f"Compiling tool description for function: {next_node.func.__name__}")

            if force_load or not os.path.exists(func_name):
                os.makedirs(self.tool_json_dir, exist_ok=True)
                try:
                    current_retry_count = 0
                    tool_desc = create_tool_desc(model=self.model, function_desc=inspect.getsource(next_node.func), api_base=self.api_base)
                    
                    while not tool_desc and current_retry_count < self.retry_json_count:
                        tool_desc = create_tool_desc(model=self.model, function_desc=inspect.getsource(next_node.func), api_base=self.api_base)
                        current_retry_count += 1

                    if not tool_desc:
                        raise ValueError(f"Tool description for {next_node.func.__name__} could not be generated, recommend generating manually and storing under {func_name}.json in {self.tool_json_dir} directory")

                    tool_desc_json = json.loads(tool_desc)
                except Exception as e:
                    self.logger.error(f"Error creating tool description for {next_node.func.__name__}: {e}")
                    raise e
                with open(func_name, 'w') as f:
                    json.dump(tool_desc_json, f)
            else:
                with open(func_name, 'r') as f:
                    tool_desc_json = json.load(f)

            next_node.tool_description = tool_desc_json
            next_node.compile()


    def run(self, **kwargs) -> any:
        if not self.next_nodes:
            raise ValueError("Next nodes not specified for LLM call")

        if not self.compiled:
            raise ValueError("Node not compiled. Please run compile() method from the entry node first")


        if not kwargs.get('prev_output') and not kwargs.get('messages'):
            raise ValueError("No input data provided for LLM call")


        # Get existing messages or create an empty list
        messages = kwargs.get('messages', [])
        # Add previous output as a user message if available
        if 'prev_output' in kwargs:
            messages.append({'role': 'user', 'content': kwargs.pop('prev_output')})
        
        # Update kwargs with the final messages list
        kwargs['messages'] = messages

        try:
            # The 'messages' param is passed in through the kwargs
            response = call_llm_tool(model=self.model, tools=[node.tool_description for node in self.next_nodes.values()], api_base=self.api_base, **kwargs)
            tool_calls = getattr(response, 'tool_calls', None)
            if not tool_calls:
                raise ValueError("No tool calls received from LLM tool response")

            # TODO: Should there be a pattern for restricting calls - error if multiple?
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                next_node = self.next_nodes.get(function_name)
                if not next_node:
                    raise KeyError(f"Function name '{function_name}' not found in next_nodes. Something went wrong")

                # Merge user_params with function_args, giving precedence to user_params
                merged_args = {**function_args, **self.user_params}
                func_signature = inspect.signature(next_node.func)
                # TODO: Manage through derived data models 
                filtered_args = {k: v for k, v in merged_args.items() if k in func_signature.parameters}

                # TODO: Can add a return here but would become a stacked call 
                next_node.run(**filtered_args)

        except (AttributeError, json.JSONDecodeError) as e:
            raise ValueError(f"Error parsing tool call: {e}")
        except Exception as e:
            raise RuntimeError(f"LLM tool call failed: {e}")
