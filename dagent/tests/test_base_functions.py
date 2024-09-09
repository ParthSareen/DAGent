import json
import inspect
import argparse
from dagent.base_functions import *

def add_two_nums(a: int, b: int) -> int:
    return a + b

def run_llm(model, api_base=None):
    # Run `call_llm`
    output = call_llm(model, [{'role': 'user', 'content': 'add the numbers 2 and 3'}], api_base=api_base)
    print(f'{model} output:', output)

    # Create tool description for `add_two_nums` function
    desc = create_tool_desc(model=model, function_desc=inspect.getsource(add_two_nums), api_base=api_base)
    print(f'{model} tool desc:', desc, end='\n\n')

    tool_desc_json = json.loads(desc)

    # Run `call_llm_tool`
    output = call_llm_tool(model, [{'role': 'user', 'content': 'add the numbers 2 and 3 using the provided tool'}], tools=[tool_desc_json], api_base=api_base)

    tool_calls = getattr(output, 'tool_calls', None)
    if not tool_calls:
        raise ValueError("No tool calls received from LLM tool response")

    function_name = tool_calls[0].function.name
    print(f'{model} output func name:', function_name, end='\n\n')

def main():
    parser = argparse.ArgumentParser(description="Run LLM models")
    parser.add_argument('model', choices=['groq', 'ollama', 'gpt4'], help="Select the model to run")
    args = parser.parse_args()

    if args.model == 'groq':
        run_llm('groq/llama3-70b-8192')
    elif args.model == 'ollama':
        run_llm('ollama_chat/mistral', api_base="http://localhost:11434")
    elif args.model == 'gpt4':
        run_llm('gpt-4-0125-preview')

if __name__ == "__main__":
    main()
