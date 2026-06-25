import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = StdioServerParameters(
    command=sys.executable,
    args=[str(Path(__file__).parent / "tools.py")],
)


async def main():
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # ── List available tools ─────────────────────────────────────
            response = await session.list_tools()
            print("=== Available tools ===")
            for tool in response.tools:
                print(f"\nname:        {tool.name}")
                print(f"description: {tool.description}")
                print(f"input_schema:\n{json.dumps(tool.inputSchema, indent=2)}")

            # ── Call calculator ──────────────────────────────────────────
            print("\n\n=== calculator calls ===")
            expressions = ["2 + 3", "(3 + 4) * 2", "2 ** 8", "5 / 0"]
            for expr in expressions:
                result = await session.call_tool("calculator", {"expression": expr})
                print(f"  {result.content[0].text}")

            # ── Call web_search ──────────────────────────────────────────
            print("\n=== web_search calls ===")
            queries = [
                {"query": "Python tutorials", "num_results": 2},
                {"query": "machine learning basics"},
                {"query": "Who is Claude?"},
            ]
            for params in queries:
                result = await session.call_tool("web_search", params)
                print(f"\n{result.content[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
