
"""
This example demonstrates the main concepts of the dagent library using a local model:
1. Function Nodes: Represent individual operations in the workflow.
2. Decision Nodes: Use AI models to make decisions and route the workflow.
3. Node Linking: Connect nodes to create a directed acyclic graph (DAG).
4. Compilation: Prepare the DAG for execution.
5. Execution: Run the workflow starting from an entry point.
"""

from dagent import DecisionNode, FunctionNode
import argparse

def add_two_nums(a: int, b: int) -> int:
    """A simple function to add two numbers."""
    return a + b

def multiply_two_nums(a: int, b: int) -> int:
    """A simple function to multiply two numbers."""
    return a * b

def print_result(prev_output: int) -> None:
    """
    Print the result from a previous node.
    
    Note: `prev_output` is automatically passed from the previous node.
    """
    print(prev_output)
    return prev_output

def entry_func(input: str) -> str:
    """Entry point function for the workflow."""
    return input

def main():

    # Initialize Function Nodes for basic arithmetic operations and result printing
    add_two_nums_node = FunctionNode(func=add_two_nums)
    multiply_two_nums_node = FunctionNode(func=multiply_two_nums)
    print_result_node = FunctionNode(func=print_result)

    # Initialize the entry point of the workflow
    entry_node = FunctionNode(func=entry_func)

    # Initialize a Decision Node configured to use a local AI model for decision-making
    decision_node = DecisionNode(model='ollama_chat/llama3.1', api_base="http://localhost:11434")

    # Link Nodes to define the workflow structure
    entry_node.next_nodes = [decision_node]
    decision_node.next_nodes = [add_two_nums_node, multiply_two_nums_node]
    add_two_nums_node.next_nodes = [print_result_node]
    multiply_two_nums_node.next_nodes = [print_result_node]

    # Compile the DAG to prepare it for execution
    entry_node.compile(force_load=False)

    # Execute the DAG in a loop to process user input dynamically
    while True:
        user_input = input("Enter your command: ")
        entry_node.run(input=user_input)

if __name__ == "__main__":
    main()
