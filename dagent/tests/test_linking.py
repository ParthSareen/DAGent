import unittest
from unittest.mock import patch, MagicMock
from dagent import DecisionNode, FunctionNode

def add_two_nums(a: int, b: int) -> int:
    return a + b

def multiply_two_nums(a: int, b: int) -> int:
    return a * b

class TestLinking(unittest.TestCase):
    def setUp(self):
        self.add_node = FunctionNode(func=add_two_nums)
        self.multiply_node = FunctionNode(func=multiply_two_nums)
        self.decision_node = DecisionNode(model='gpt-4-0125-preview', api_base=None)
        
        self.decision_node.next_nodes = {
            'add_two_nums': self.add_node,
            'multiply_two_nums': self.multiply_node
        }

    @patch('dagent.DecisionNode.call_llm_tool')
    def test_decision_node_linking(self, mock_call_llm_tool):
        # Mock the LLM response to simulate choosing the add_two_nums function
        mock_response = MagicMock()
        mock_function = MagicMock()
        mock_function.name = 'add_two_nums'
        mock_function.arguments = '{"a": 2, "b": 3}'
        mock_response.tool_calls = [MagicMock(function=mock_function)]
        mock_call_llm_tool.return_value = mock_response

        # Compile the decision node
        self.decision_node.compile()

        # Run the decision node
        with patch.object(self.add_node, 'run') as mock_add_run:
            self.decision_node.run(messages=[{'role': 'user', 'content': 'Add 2 and 3'}])

            # Assert that the add_two_nums function was called
            mock_add_run.assert_called_once_with(a=2, b=3)

    @patch('dagent.DecisionNode.call_llm_tool')
    def test_decision_node_linking_multiply(self, mock_call_llm_tool):
        # Mock the LLM response to simulate choosing the multiply_two_nums function
        mock_response = MagicMock()
        mock_function = MagicMock()
        mock_function.name = 'multiply_two_nums'
        mock_function.arguments = '{"a": 4, "b": 5}'
        mock_response.tool_calls = [MagicMock(function=mock_function)]
        mock_call_llm_tool.return_value = mock_response

        # Compile the decision node
        self.decision_node.compile()

        # Run the decision node
        with patch.object(self.multiply_node, 'run') as mock_multiply_run:
            self.decision_node.run(messages=[{'role': 'user', 'content': 'Multiply 4 and 5'}])

            # Assert that the multiply_two_nums function was called
            mock_multiply_run.assert_called_once_with(a=4, b=5)

if __name__ == '__main__':
    unittest.main()