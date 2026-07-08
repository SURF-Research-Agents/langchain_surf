# pip install -qU deepagents langchain-google-genai
from deepagents import create_deep_agent
from langchain_surf import ChatWillma   
from typing import Literal
from langchain.tools import tool
from dotenv import load_dotenv
import os 
from tavily import TavilyClient

load_dotenv('/Users/renau001/Documents/projects/ai/SRA/.env')

api_key = os.getenv("AIHUB_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")
base_url = "https://willma.surf.nl/api/v0"
model = "default-text-medium"
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


model = ChatWillma(
    model=model,
    temperature=0.1,
    max_tokens=1000,
    timeout=30,
    api_key=api_key,
)


# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

agent = create_deep_agent(
    model=model,
    tools=[internet_search],
    system_prompt=research_instructions,
)

# Run the agent
result = agent.invoke(
    {"messages": [{"role": "user", "content": "what is langgraph"}]}
)

# Print the agent's response
print(result["messages"][-1].content)