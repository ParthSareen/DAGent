import unittest
import os
import shutil
from unittest.mock import patch, MagicMock
from dagent.DecisionNode import DecisionNode
from dagent.FunctionNode import FunctionNode

class TestDecisionNode(unittest.TestCase):
    def setUp(self):
        self.test_dir = 'test_tool_json'
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('dagent.DecisionNode.call_llm_tool')
    @patch('dagent.DecisionNode.create_tool_desc')
    def test_decision_node(self, mock_create_tool_desc, mock_call_llm_tool):
        # Mock function for testing
        def test_function(arg1, arg2):
            return f"Result: {arg1}, {arg2}"

        # Mock create_tool_desc to return a valid tool description
        mock_create_tool_desc.return_value = '{"type": "function", "function": {"name": "test_function", "parameters": {"type": "object", "properties": {"arg1": {"type": "string"}, "arg2": {"type": "string"}}, "required": ["arg1", "arg2"]}}}'

        # Mock call_llm_tool to return a valid response
        mock_response = MagicMock()
        mock_tool_call = MagicMock()
        mock_tool_call.function = MagicMock()
        mock_tool_call.function.name = 'test_function'
        mock_tool_call.function.arguments = '{"arg1": "hello", "arg2": "world"}'
        mock_response.tool_calls = [mock_tool_call]
        mock_call_llm_tool.return_value = mock_response

        # Create DecisionNode with FunctionNode as next node
        function_node = FunctionNode(func=test_function)
        decision_node = DecisionNode(next_nodes={'test_function': function_node})

        # Compile the decision node
        decision_node.compile(tool_json_dir=self.test_dir)

        # Check if the tool description file was created
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'test_function.json')))

        # Run the decision node
        with patch.object(function_node, 'run') as mock_function_run:
            decision_node.run(messages=[{'role': 'user', 'content': 'Test message'}])

        # Assert that the function node's run method was called with correct arguments
        mock_function_run.assert_called_once_with(arg1='hello', arg2='world')

        # Assert that create_tool_desc and call_llm_tool were called
        mock_create_tool_desc.assert_called_once()
        mock_call_llm_tool.assert_called_once()

if __name__ == '__main__':
    unittest.main()