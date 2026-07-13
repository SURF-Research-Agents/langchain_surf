import os
from typing import Optional
import json 
from langchain.agents import create_agent
from langchain_surf.tools.hpc_tools import tool
from langchain_surf.chat_models.chat_willma import ChatWillma
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../../.env")

api_key = os.getenv("AIHUB_API_KEY")
model = "default-text-large"
slurm_jwt = os.getenv("SLURM_JWT")
os_key = os.getenv("OS_KEY")
os_secret = os.getenv("OS_SECRET_KEY")


slurm_data = {
    "url": "https://slurm.snellius.surf.nl",
    "api_ver": "v0.0.43",
    "user_name": "nicolasr",
    "slurm_jwt": slurm_jwt,
}

os_data = {
    "url": "https://objectstore.surf.nl",
    "os_access_key": os_key,
    "os_secret_key": os_secret,
}


model = ChatWillma(
    model=model,
    temperature=0.1,
    max_tokens=1000,
    timeout=30,
    api_key=api_key,
)

hpc_opt = {
    'slurm_data': slurm_data,
    'os_data': os_data
}

@tool(hpc=hpc_opt)
def calculate_expression(expression):
    """Evaluate the mathematical expression and return the result."""
    
    import ast
    import operator
    from collections.abc import Callable

    OPERATORS: dict[type[ast.operator], Callable] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }

    def _eval_expr(node: ast.AST) -> float:
        """Evaluate an AST node recursively."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int or float):
                return float(node.value)
            error_msg = f"Unsupported constant type: {type(node.value).__name__}"
            raise TypeError(error_msg)
        if isinstance(node, ast.Constant):  # For backwards compatibility
            if isinstance(node.n, int or float):
                return float(node.n)
            error_msg = f"Unsupported number type: {type(node.n).__name__}"
            raise TypeError(error_msg)

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in OPERATORS:
                error_msg = f"Unsupported binary operator: {op_type.__name__}"
                raise TypeError(error_msg)

            left = _eval_expr(node.left)
            right = _eval_expr(node.right)
            return OPERATORS[op_type](left, right)

        error_msg = f"Unsupported operation or expression type: {type(node).__name__}"
        raise TypeError(error_msg)
    
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_expr(tree.body)

        formatted_result = f"{float(result):.6f}".rstrip("0").rstrip(".")
        return {'result': formatted_result}

    except ZeroDivisionError:
        error_message = "Error: Division by zero"
        return {'error': error_message, 'input': expression}

    except (SyntaxError, TypeError, KeyError, ValueError, AttributeError, OverflowError) as e:
        error_message = f"Invalid expression: {e!s}"
        return {'error': error_message, 'input': expression}


@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

@tool
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    return f"Weather in {location}: Sunny, 72°F"

agent = create_agent(model, 
                     tools=[search, get_weather, calculate_expression],
                     system_prompt="You are a helpful assistant. Be concise and accurate.")


result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's (12+3)*4?"}]}
)
print(result)
