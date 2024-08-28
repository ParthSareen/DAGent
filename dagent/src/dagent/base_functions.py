import inspect
from litellm import completion
from openai import OpenAI
# For more info: https://litellm.vercel.app/docs/completion/input

client = OpenAI()

def call_llm_tool(model, messages, tools, api_base=None, **kwargs):
    response = completion(
        model=model,
        messages=messages,
        tools=tools,
        api_base=api_base,
        tool_choice='required'
    )
    return response.choices[0].message
    

def create_tool_desc(model, function_desc, api_base=None):
    example = {
            "type": "function",
            "function": {
                "name": "get_calendar_events",
                "description": "Get calendar events within a specified time range",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_time": {
                            "type": "string",
                            "description": "The start time for the event search, in ISO format",
                        },
                        "end_time": {
                            "type": "string",
                            "description": "The end time for the event search, in ISO format",
                        },
                    },
                    "required": ["start_time", "end_time"],
                },
            }
    }
    messages = [{"role": "user", "content": "Create a json for the attached function: {} using the following pattern for the json: {}. Don't add anything extra".format(function_desc, example)}]
    response = completion(
        model=model,
        response_format={"type":"json_object"},
        messages=messages,
        api_base=api_base
    )
    return response.choices[0].message.content


def call_llm(model, messages, api_base=None, **kwargs):
    response = completion(
        model=model,
        messages=messages,
        api_base=api_base
    )
    return response.choices[0].message.content

desc = {
    "type": "function",
    "function": {
        "name": "add_two_nums",
        "description": "Adds two integer numbers",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "The first number to add"
                },
                "b": {
                    "type": "integer",
                    "description": "The second number to add"
                }
            },
            "required": [
                "a",
                "b"
            ]
        }
    }
}
# output = call_llm_tool('groq/llama3-8b-8192', [{'role': 'user', 'content': 'add the numbers 2 and 3'}], tools=[desc])

# tool_calls = getattr(output, 'tool_calls', None)
# if not tool_calls:
#     raise ValueError("No tool calls received from LLM tool response")

# function_name = tool_calls[0].function.name
# print(function_name)

output = call_llm_tool('ollama_chat/hermes3', [{'role': 'user', 'content': 'add the numbers 2 and 3'}], tools=[desc])

tool_calls = getattr(output, 'tool_calls', None)
if not tool_calls:
    raise ValueError("No tool calls received from LLM tool response")

function_name = tool_calls[0].function.name
print(function_name)