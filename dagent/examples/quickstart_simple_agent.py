
from dagent import DecisionNode, FunctionNode
import logging

"""
This example demonstrates the main concepts of the dagent library:
1. Function Nodes: Represent individual operations in the workflow.
2. Decision Nodes: Use AI models to make decisions and route the workflow.
3. Node Linking: Connect nodes to create a directed acyclic graph (DAG).
4. Compilation: Prepare the DAG for execution.
5. Execution: Run the workflow starting from an entry point.
"""

# Configure root logger to save logs to file

# Can enable logging below to save logs to file
# logging.basicConfig(level=logging.INFO, 
                    # format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    # handlers=[logging.FileHandler('dagent_logs.log'), logging.StreamHandler()])

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
    # Setup Function Nodes
    """
    FunctionNodes wrap regular Python functions, allowing them to be used in the DAG.
    """
    add_two_nums_node = FunctionNode(func=add_two_nums)
    multiply_two_nums_node = FunctionNode(func=multiply_two_nums)
    print_result_node = FunctionNode(func=print_result)
    entry_node = FunctionNode(func=entry_func)

    # Setup Decision Node
    """
    DecisionNodes use AI models to make routing decisions in the workflow.
    """
    decision_node = DecisionNode(model='gpt-4-0125-preview', api_base=None)

    # Link Nodes
    """
    Nodes are connected by setting their `next_nodes` attribute.
    This creates the structure of the directed acyclic graph (DAG).
    """
    entry_node.next_nodes = [decision_node]

    decision_node.next_nodes = [
        add_two_nums_node,
        multiply_two_nums_node,
    ]

    add_two_nums_node.next_nodes = [print_result_node]
    multiply_two_nums_node.next_nodes = [print_result_node]

    # Compile the DAG
    """
    Compilation prepares the DAG for execution, ensuring all nodes are properly linked.
    """
    entry_node.compile(force_load=True)

    # Execute the DAG
    while True:
        user_input = input("Enter your command: ")
        entry_node.run(input=user_input)

if __name__ == "__main__":
    main()
