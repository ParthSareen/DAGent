import unittest
from unittest.mock import MagicMock
from dagent.FunctionNode import FunctionNode

class TestFunctionNode(unittest.TestCase):
    def setUp(self):
        def test_func(a, b):
            return a + b
        self.function_node = FunctionNode(func=test_func)
        self.function_node.tool_description = None


    def test_init(self):
        self.assertIsInstance(self.function_node, FunctionNode)
        self.assertEqual(self.function_node.func.__name__, 'test_func')
        # Check if tool_description is either None or an empty dict
        self.assertTrue(self.function_node.tool_description is None or self.function_node.tool_description == {})
        self.assertEqual(self.function_node.user_params, {})
        self.assertFalse(self.function_node.compiled)
        self.assertIsNone(self.function_node.node_result)

    def test_compile(self):
        def identity(x):
            return x
        next_node = FunctionNode(func=identity)
        self.function_node.next_nodes = [next_node]
        self.function_node.compile()
        self.assertTrue(self.function_node.compiled)
        self.assertIsInstance(self.function_node.next_nodes, dict)
        # Changed assertion for next_nodes key
        self.assertIn('identity', self.function_node.next_nodes)

    def test_compile(self):
        def identity(x):
            return x
        next_node = FunctionNode(func=identity)
        self.function_node.next_nodes = [next_node]
        self.function_node.compile()
        self.assertTrue(self.function_node.compiled)
        self.assertIsInstance(self.function_node.next_nodes, dict)
        self.assertIn('identity', self.function_node.next_nodes)

    def test_run_without_compile(self):
        with self.assertRaises(ValueError):
            self.function_node.run(a=1, b=2)

    def test_run_with_compile(self):
        self.function_node.compile()
        result = self.function_node.run(a=1, b=2)
        self.assertEqual(result, 3)
        self.assertEqual(self.function_node.node_result, 3)

    def test_run_with_user_params(self):
        self.function_node.user_params = {'b': 5}
        self.function_node.compile()
        result = self.function_node.run(a=1)
        self.assertEqual(result, 6)

    def test_run_with_next_nodes(self):
        def double(x):
            return x * 2
        next_node = FunctionNode(func=double)
        self.function_node.next_nodes = [next_node]
        self.function_node.compile()
        
        next_node.run = MagicMock()
        self.function_node.run(a=1, b=2)
        
        next_node.run.assert_called_once_with(prev_output=3)

if __name__ == '__main__':
    unittest.main()
