import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient  
from langchain.agents import create_agent

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent
from langchain_surf import ChatWillma
import os 
import json 

load_dotenv('/Users/renau001/Documents/projects/ai/SRA/.env')

api_key = os.getenv("AIHUB_API_KEY")
base_url = "https://willma.surf.nl/api/v0"
model = "default-text-large"


model = ChatWillma(
    model=model,
    temperature=0.1,
    max_tokens=100000,
    timeout=30,
    api_key=api_key,
)

async def main():
    client = MultiServerMCPClient(
        {
            # "math": {
            #     "transport": "streamable-http",  # Local subprocess communication
            #     # "transport": "stdio",  # HTTP-based remote server
            #     "url": "http://localhost:8000/mcp",  # Ensure you start your math server on port 8000
            #     # "command": "python",
            #     # Absolute path to your math_server.py file
            #     # "args": ["/Users/renau001/Documents/projects/ai/SRA/langchain_surf/docs/examples/mcp/math_server.py"],
            # },
            # "weather": {
            #     "transport": "streamable-http",  # HTTP-based remote server
            #     # Ensure you start your weather server on port 8000
            #     "url": "http://localhost:8000/mcp",
            # }
            "tool-universe": {
                "transport": "streamable-http",  # HTTP-based remote server
                # Ensure you start your weather server on port 8000
                "url": "http://localhost:8000/mcp",
            }
        }
    )

    tools = await client.get_tools()

    agent = create_deep_agent(
        model=model,
        tools=tools,
    )
    # math_response = await agent.ainvoke(
    #     {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]}
    # )
    # weather_response = await agent.ainvoke(
    #     {"messages": [{"role": "user", "content": "what's the weather like in NYC?"}]}
    # )
    tu_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "which tools are available for biology research?"}]}
    )
    # print(math_response)
    print(tu_response['messages'][-1].content)
    
    # print(json.dumps(tu_response, indent=4))  # Pretty print the response
if __name__ == "__main__":
    asyncio.run(main())