from dagent import DecisionNode, FunctionNode, call_llm 
import logging

example_schema = """
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    registration_date DATE
);

CREATE TABLE Products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER
);

CREATE TABLE Orders (
    order_id INTEGER PRIMARY KEY,
    user_id INTEGER,
    order_date DATE,
    total_amount DECIMAL(10, 2),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE OrderItems (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price_per_unit DECIMAL(10, 2),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (product_id) REFERENCES Products(product_id)
);

INSERT INTO Users (username, email, registration_date) VALUES
('john_doe', 'john@example.com', '2023-01-15'),
('jane_smith', 'jane@example.com', '2023-02-20'),
('bob_johnson', 'bob@example.com', '2023-03-10');

INSERT INTO Products (product_name, price, stock_quantity) VALUES
('Laptop', 999.99, 50),
('Smartphone', 599.99, 100),
('Headphones', 79.99, 200);

INSERT INTO Orders (user_id, order_date, total_amount) VALUES
(1, '2023-04-01', 1079.98),
(2, '2023-04-15', 599.99),
(3, '2023-04-30', 159.98);

INSERT INTO OrderItems (order_id, product_id, quantity, price_per_unit) VALUES
(1, 1, 1, 999.99),
(1, 3, 1, 79.99),
(2, 2, 1, 599.99),
(3, 3, 2, 79.99);
"""


logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('dagent_logs.log'), logging.StreamHandler()])

def get_user_input() -> str:
    """Get user input from the command line."""
    user_input = input("Enter your command: ")
    return user_input

def get_database_schema(prev_output: str) -> str:
    return example_schema

def generate_sql(prev_output: str, database_schema: str) -> str:
    """Generate SQL from the user input."""
    sql = call_llm(model='ollama_chat/llama3.1', api_base="http://localhost:11434", messages=[{"role": "user", "content": f"Generate SQL from the user input: {prev_output} and the following database schema: {database_schema}"}])
    print('generated sql: ', sql)
    return sql

def show_results(prev_output: str) -> str:
    print('results: ', prev_output)

    
get_user_input_node = FunctionNode(func=get_user_input)
get_database_schema_node = FunctionNode(func=get_database_schema)
generate_sql_node = FunctionNode(func=generate_sql, user_params={"database_schema": example_schema})
show_results_node = FunctionNode(func=show_results)

decision_node = DecisionNode(model='ollama_chat/llama3.1', api_base="http://localhost:11434")

get_user_input_node.next_nodes = [decision_node]
decision_node.next_nodes = [get_database_schema_node, generate_sql_node]
get_database_schema_node.next_nodes = [generate_sql_node]
generate_sql_node.next_nodes = [show_results_node]


if __name__ == "__main__":
    get_user_input_node.compile(force_load=False)
    get_user_input_node.run()