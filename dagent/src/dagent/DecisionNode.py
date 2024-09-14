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
        retry_json_count: int = 3,
        max_tool_calls: int | None = None

    ):
        super().__init__(func, next_nodes)
        self.user_params = user_params or {}
        self.logger = logging.getLogger(__name__)
        self.compiled = False
        self.api_base = api_base
        self.model = model
        self.tool_json_dir = tool_json_dir
        self.retry_json_count = retry_json_count
        self.max_tool_calls = max_tool_calls
        self.logger.info(f"DecisionNode initialized with model: {model}, api_base: {api_base}, max_tool_calls: {max_tool_calls}")
    

    def compile(self, force_load=False) -> None:
        self.logger.info("Starting compilation process")
        self.compiled = True

        if isinstance(self.next_nodes, list):
            self.next_nodes = {node.func.__name__: node for node in self.next_nodes}
            self.logger.debug(f"Converted next_nodes list to dictionary: {self.next_nodes.keys()}")

        for _, next_node in self.next_nodes.items():
            func_name = os.path.join(self.tool_json_dir, next_node.func.__name__ + '.json')
            self.logger.info(f"Compiling tool description for function: {next_node.func.__name__}")

            if force_load or not os.path.exists(func_name):
                self.logger.debug(f"Creating new tool description for {next_node.func.__name__}")
                os.makedirs(self.tool_json_dir, exist_ok=True)
                try:
                    current_retry_count = 0
                    tool_desc = create_tool_desc(model=self.model, function_desc=inspect.getsource(next_node.func), api_base=self.api_base)
                    
                    while not tool_desc and current_retry_count < self.retry_json_count:
                        self.logger.warning(f"Retry {current_retry_count + 1} for creating tool description of {next_node.func.__name__}")
                        tool_desc = create_tool_desc(model=self.model, function_desc=inspect.getsource(next_node.func), api_base=self.api_base)
                        current_retry_count += 1

                    if not tool_desc:
                        error_msg = f"Tool description for {next_node.func.__name__} could not be generated, recommend generating manually and storing under {func_name}.json in {self.tool_json_dir} directory"
                        self.logger.error(error_msg)
                        raise ValueError(error_msg)

                    tool_desc_json = json.loads(tool_desc)
                    self.logger.debug(f"Successfully created tool description for {next_node.func.__name__}")
                except Exception as e:
                    self.logger.error(f"Error creating tool description for {next_node.func.__name__}: {e}")
                    raise e
                with open(func_name, 'w') as f:
                    json.dump(tool_desc_json, f)
                    self.logger.info(f"Saved tool description for {next_node.func.__name__} to {func_name}")
            else:
                self.logger.info(f"Loading existing tool description for {next_node.func.__name__} from {func_name}")
                with open(func_name, 'r') as f:
                    tool_desc_json = json.load(f)

            next_node.tool_description = tool_desc_json
            next_node.compile()
        self.logger.info("Compilation process completed successfully for DecisionNode")


    def run(self, **kwargs) -> any:
        self.logger.info("Starting DecisionNode run")
        if not self.next_nodes:
            error_msg = "Next nodes not specified for LLM call"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        if not self.compiled:
            error_msg = "Node not compiled. Please run compile() method from the entry node first"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        if not kwargs.get('prev_output') and not kwargs.get('messages'):
            error_msg = "No input data provided for LLM call"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Get existing messages or create an empty list
        messages = self.user_params.get('messages', kwargs.get('messages', []))
        # Add previous output as a user message if available
        if 'prev_output' in kwargs:
            messages.append({'role': 'user', 'content': str(kwargs['prev_output'])})
        
        # Update kwargs with the final messages list
        kwargs['messages'] = messages
        self.logger.info(f"Prepared messages for LLM call: {messages}")

        try:
            self.logger.info(f"Calling LLM tool with model: {self.model}")
            # The 'messages' param is passed in through the kwargs
            response = call_llm_tool(model=self.model, tools=[node.tool_description for node in self.next_nodes.values()], api_base=self.api_base, **kwargs)
            tool_calls = getattr(response, 'tool_calls', None)
            if not tool_calls:
                error_msg = "No tool calls received from LLM tool response"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            self.logger.info(f"Received {len(tool_calls)} tool call(s) from LLM")
            self.logger.info(f"Tool calls: {tool_calls}")
            if self.logger.getEffectiveLevel() == logging.DEBUG:
                proceed = input("Debug mode is active. Do you want to proceed with the tool calls? (yes(y)/no(n)): ")
                print('proceed: ',proceed)
                if proceed.lower() not in ['yes', 'y']:
                    self.logger.debug("\nUser chose not to proceed with the tool calls.")
                    return

            # Apply max_tool_calls constraint if set
            if self.max_tool_calls is not None:
                tool_calls = tool_calls[:self.max_tool_calls]
                self.logger.info(f"Constrained to {len(tool_calls)} tool call(s) due to max_tool_calls setting")

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                self.logger.debug(f"Processing tool call for function: {function_name} with arguments: {function_args}")

                next_node = self.next_nodes.get(function_name)
                if not next_node:
                    error_msg = f"Function name '{function_name}' not found in next_nodes. Something went wrong"
                    self.logger.error(error_msg)
                    raise KeyError(error_msg)

                # Merge user_params with function_args, giving precedence to user_params
                merged_args = {**function_args, **self.user_params}
                # Print kwargs for debugging
                self.logger.info(f"Current kwargs: {kwargs}")
                print(f"Current kwargs: {kwargs}")

                if 'prev_output' in kwargs:
                    merged_args['prev_output'] = kwargs['prev_output']

                func_signature = inspect.signature(next_node.func)

                # TODO: Manage through derived data models 
                filtered_args = {k: v for k, v in merged_args.items() if k in func_signature.parameters}
                self.logger.info(f"Filtered arguments for {function_name}: {filtered_args}")

                self.logger.info(f"Executing next node: {function_name}")
                next_node.run(**filtered_args)

        except (AttributeError, json.JSONDecodeError) as e:
            error_msg = f"Error parsing tool call: {e}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"LLM tool call failed: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        self.logger.info("DecisionNode run completed successfully")
