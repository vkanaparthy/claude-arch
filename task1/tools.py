import ast
import operator
from typing import Annotated
from pydantic import Field
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("tools-server")

TOOLS = [
  {
    "name": "calculator",
    "description": "Evaluates a mathematical expression",
    "input_schema": {
      "type": "object",
      "properties": { "expression": { "type": "string" } },
      "required": ["expression"]
    }
  },
    {
    "name": "web_search",
    "description": "Performs a web search and returns relevant results",
    "input_schema": {
      "type": "object",
      "properties": { "query": { "type": "string" } },
      "required": ["query"]
    }
  }
]

# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        op = SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op = SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(_eval_node(node.operand))
    raise ValueError(f"Unsupported expression type: {type(node).__name__}")


@mcp.tool(
    name="calculator",
    description=(
        "Evaluate a mathematical expression and return the result. "
        "Supports +, -, *, /, // (floor division), % (modulo), and ** (exponentiation). "
        "Use this whenever the user asks you to compute or calculate a numeric value."
    ),
)
def calculator(
    expression: Annotated[
        str,
        Field(description="A mathematical expression to evaluate, e.g. '2 + 3 * (4 - 1)'."),
    ],
) -> str:
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval_node(tree.body)
        return f"{expression} = {result}"
    except ZeroDivisionError:
        return f"Error: Division by zero in '{expression}'"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Web search
# ---------------------------------------------------------------------------

MOCK_DATABASE = {
    "python": [
        {"title": "Python Official Docs", "url": "https://docs.python.org", "snippet": "The official home of the Python programming language."},
        {"title": "Real Python", "url": "https://realpython.com", "snippet": "Python tutorials and articles for all skill levels."},
        {"title": "Python on Wikipedia", "url": "https://en.wikipedia.org/wiki/Python_(programming_language)", "snippet": "Python is a high-level, general-purpose programming language."},
    ],
    "machine learning": [
        {"title": "scikit-learn", "url": "https://scikit-learn.org", "snippet": "Simple and efficient tools for predictive data analysis."},
        {"title": "TensorFlow", "url": "https://tensorflow.org", "snippet": "An end-to-end open source machine learning platform."},
        {"title": "ML on Wikipedia", "url": "https://en.wikipedia.org/wiki/Machine_learning", "snippet": "Machine learning is a field of study in artificial intelligence."},
    ],
    "claude": [
        {"title": "Anthropic", "url": "https://anthropic.com", "snippet": "Anthropic is an AI safety company behind Claude."},
        {"title": "Claude API Docs", "url": "https://docs.anthropic.com", "snippet": "Documentation for the Claude API and SDKs."},
    ],
}

DEFAULT_RESULTS = [
    {"title": "Result 1", "url": "https://example.com/1", "snippet": "A relevant result for your query."},
    {"title": "Result 2", "url": "https://example.com/2", "snippet": "Another relevant result for your query."},
    {"title": "Result 3", "url": "https://example.com/3", "snippet": "Yet another relevant result for your query."},
]


@mcp.tool(
    name="web_search",
    description=(
        "Search the web for information and return a list of relevant results. "
        "Each result includes a title, URL, and short snippet. "
        "Use this when the user asks for current information or wants to look something up online."
    ),
)
def web_search(
    query: Annotated[
        str,
        Field(description="The search query string, e.g. 'Python async tutorial'."),
    ],
    num_results: Annotated[
        int,
        Field(default=3, description="Maximum number of results to return.", ge=1, le=10),
    ] = 3,
) -> str:
    query_lower = query.lower()
    results = None
    for keyword, hits in MOCK_DATABASE.items():
        if keyword in query_lower:
            results = hits
            break

    if results is None:
        results = DEFAULT_RESULTS

    hits = results[:num_results]
    lines = [f"Results for '{query}' ({len(hits)} of {len(results)} found):\n"]
    for i, h in enumerate(hits, 1):
        lines.append(f"{i}. {h['title']}")
        lines.append(f"   {h['url']}")
        lines.append(f"   {h['snippet']}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
