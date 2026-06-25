import sys
import json
from pathlib import Path

import anthropic

# Import the actual tool implementations from tools.py in the same directory.
sys.path.insert(0, str(Path(__file__).parent))
from tools import calculator, web_search  # noqa: E402

MODEL = "claude-opus-4-8"

TOOLS: list[anthropic.types.ToolParam] = [
    {
        "name": "calculator",
        "description": (
            "Evaluate a mathematical expression and return the result. "
            "Supports +, -, *, /, // (floor division), % (modulo), and ** (exponentiation). "
            "Use this whenever the user asks you to compute or calculate a numeric value."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A mathematical expression to evaluate, e.g. '2 + 3 * (4 - 1)'.",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Search the web for information and return a list of relevant results. "
            "Each result includes a title, URL, and short snippet. "
            "Use this when the user asks for current information or wants to look something up online."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string, e.g. 'Python async tutorial'.",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
]


def dispatch_tool(name: str, tool_input: dict) -> str:
    if name == "calculator":
        return calculator(**tool_input)
    if name == "web_search":
        return web_search(**tool_input)
    raise ValueError(f"Unknown tool: {name!r}")


def run(user_message: str) -> str:
    client = anthropic.Anthropic()
    messages: list[anthropic.types.MessageParam] = [
        {"role": "user", "content": user_message}
    ]

    while True:
        response = (
            client.messages.create(
                model=MODEL,
                max_tokens=16000,
                thinking={"type": "adaptive"},
                tools=TOOLS,
                messages=messages,
            )
        )

        if response.stop_reason == "end_turn":
            # Return the last text block.
            for block in reversed(response.content):
                if block.type == "text":
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            # Collect tool calls.
            tool_uses = [b for b in response.content if b.type == "tool_use"]

            # Append assistant turn (full content, including thinking blocks).
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool and build the user tool_result turn.
            tool_results: list[anthropic.types.ToolResultBlockParam] = []
            for tool_use in tool_uses:
                print(f"  [tool] {tool_use.name}({json.dumps(tool_use.input)})")
                result = dispatch_tool(tool_use.name, tool_use.input)
                print(f"  [result] {result[:120]}{'...' if len(result) > 120 else ''}")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": result,
                    }
                )

            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason — bail out.
        raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason!r}")


def main() -> None:
    prompts = [
        "What is (123 * 456) + (789 / 3)?",
        "Search for information about machine learning and then compute 2 ** 10.",
        "What can you find about Claude?",
    ]

    for prompt in prompts:
        print(f"\n{'=' * 60}")
        print(f"User: {prompt}")
        print("-" * 60)
        answer = run(prompt)
        print(f"Claude: {answer}")


if __name__ == "__main__":
    main()
