"""Demonstrates `call_llm` and `call_llm_tool` with different models and configs."""

from dagent.base_functions import *

# Run `call_llm` with 'groq/llama3-8b-8192' model
output = call_llm('groq/llama3-8b-8192', [{'role': 'user', 'content': 'add the numbers 2 and 3'}])
print('groq output:', output)

# Run `call_llm` with 'ollama_chat/mistral' model locally
output = call_llm('ollama_chat/mistral', [{'role': 'user', 'content': 'add the numbers 2 and 3'}], api_base="http://localhost:11434") 
print('ollama output:', output)

# Create tool description for `add_two_nums` function
def add_two_nums(a: int, b: int) -> int:
    return a + b

desc = create_tool_desc(model='groq/llama3-8b-8192', function_desc=inspect.getsource(add_two_nums))
print('groq tool desc:', desc)

desc = create_tool_desc(model='ollama_chat/mistral', function_desc=inspect.getsource(add_two_nums), api_base="http://localhost:11434")
print('ollama tool desc:', desc)

# Run `call_llm_tool` with 'groq/llama3-8b-8192' model
output = call_llm_tool('groq/llama3-8b-8192', [{'role': 'user', 'content': 'add the numbers 2 and 3'}], tools=[desc])

tool_calls = getattr(output, 'tool_calls', None)
if not tool_calls:
    raise ValueError("No tool calls received from LLM tool response")

function_name = tool_calls[0].function.name
print('grok output func name:', function_name)

# Run `call_llm_tool` with 'ollama_chat/hermes3' model
output = call_llm_tool('ollama_chat/hermes3', [{'role': 'user', 'content': 'add the numbers 2 and 3'}], tools=[desc])

tool_calls = getattr(output, 'tool_calls', None)
if not tool_calls:
    raise ValueError("No tool calls received from LLM tool response")

function_name = tool_calls[0].function.name
print('ollama output func name:', function_name)

