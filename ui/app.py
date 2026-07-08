from flask import Flask, Response, request
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessageChunk
from langchain_core.runnables import RunnableGenerator
import json
import time
from typing import Iterable, Literal
from uuid import uuid4
from langchain_core.prompts import ChatPromptTemplate
from langchain_surf import ChatWillma
from dotenv import load_dotenv
import os

load_dotenv('/Users/renau001/Documents/projects/ai/SRA/.env')

api_key = os.getenv("AIHUB_API_KEY")
base_url = "https://willma.surf.nl/api/v0"
model = "default-text-large"


system_fingerprint = str(uuid4())
app = Flask(__name__)


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class OpenAIRequest(BaseModel):
    model: str
    user: str
    stream: bool
    messages: list[Message]


@RunnableGenerator
def stream_openai_response(chunks: Iterable[AIMessageChunk]) -> Iterable[bytes]:
    for chunk in chunks:
        data = json.dumps({"id": chunk.id,
                           "object": 
                           "chat.completion.chunk", 
                           "created": int(time.time()), 
                           "model": model, 
                           "system_fingerprint": system_fingerprint,
                           "choices":[
                               {
                                "index": 0,
                                "delta": {"content": chunk.content},
                                "logprobs": None,
                                "finish_reason": None
                                }
                                    ]})
        b = bytes(f"data: {data}\n\n", "utf-8")
        yield b

def build_chain():
    prompt = ChatPromptTemplate.from_template("Question: {input}")
    llm = ChatWillma(
        model=model,
        temperature=0.1,
        max_tokens=1000,
        timeout=30,
        api_key=api_key,
    )
    return prompt | llm

chain = build_chain() | stream_openai_response

@app.route("/chat/completions", methods=["POST"])
def chat():
    payload = request.get_json(force=True, silent=True) or {}
    print('request:', payload)
    chat_request = OpenAIRequest(**payload)
    print('chat_request:', chat_request)
    question = chat_request.messages[-1].content
    print('question:', question)
    return Response(chain.stream(question), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(debug=True, port=8000)
