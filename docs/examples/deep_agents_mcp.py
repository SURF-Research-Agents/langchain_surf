import asyncio
import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent
from langchain_surf import ChatWillma

load_dotenv('/Users/renau001/Documents/projects/ai/SRA/.env')

api_key = os.getenv("AIHUB_API_KEY")
base_url = "https://willma.surf.nl/api/v0"
model = "default-text-medium"


model = ChatWillma(
    model=model,
    temperature=0.1,
    max_tokens=1000,
    timeout=30,
    api_key=api_key,
)

async def main():
    client = MultiServerMCPClient(
        {
            "my_server": {
                "transport": "http",
                "url": "http://127.0.0.1:7000/mcp",
            }
        }
    )
    tools = await client.get_tools()

    agent = create_deep_agent(
        model=model,
        tools=tools,
    )

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "Use the MCP server to help me."}]},
        config={"configurable": {"thread_id": "1"}},
    )

asyncio.run(main())