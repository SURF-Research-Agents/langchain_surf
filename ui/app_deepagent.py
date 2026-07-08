from flask import Flask, Response, request
from typing import Iterable, Literal, Union
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessageChunk
from deepagents import create_deep_agent
from langchain_core.runnables import RunnableGenerator
import json
import time
from typing import Iterable, Literal
from uuid import uuid4
from langchain_core.prompts import ChatPromptTemplate
from langchain_surf import ChatWillma
from dotenv import load_dotenv
import os
from tavily import TavilyClient
from langchain_surf.ui.message import Message, OpenAIRequest
from langchain_surf.ui.stream import OpenAIStream
from langchain_surf.ui.chain import DeepAgentChain

load_dotenv('/Users/renau001/Documents/projects/ai/SRA/.env')

api_key = os.getenv("AIHUB_API_KEY")
base_url = "https://willma.surf.nl/api/v0"
model = "default-text-large"
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

system_fingerprint = str(uuid4())
app = Flask(__name__)

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

openai_stream = OpenAIStream(model, system_fingerprint)
chain = DeepAgentChain(model, api_key)


chain = chain() | openai_stream

@app.route("/chat/completions", methods=["POST"])
def chat():
    payload = request.get_json(force=True, 
                               silent=True) or {}
    
    chat_request = OpenAIRequest(**payload)
    
    question = chat_request.messages[-1].content
    
    return Response(chain.stream(question), 
                    mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(debug=True, port=8000)
