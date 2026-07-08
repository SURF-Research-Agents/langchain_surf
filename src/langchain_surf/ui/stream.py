from typing import Iterable
import time
import json
from uuid import uuid4
from langchain_core.runnables import RunnableGenerator
from langchain_core.messages import AIMessageChunk


class OpenAIStream:

    def __init__(self, model, system_fingerprint):
        self.model = model
        self.system_fingerprint = system_fingerprint

    def __call__(self, chunks: Iterable[AIMessageChunk])-> Iterable[bytes]:
        return self.stream_openai_response(chunks)
    
    @staticmethod
    def format_data(chunk_id, model, system_fingerprint, content):
        return json.dumps({
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model,
                "system_fingerprint": system_fingerprint,
                "choices": [{
                    "index": 0,
                    "delta": {"content": content},
                    "logprobs": None,
                    "finish_reason": None,
                }],
            })
    
    @staticmethod
    def get_content(chunk):
        if isinstance(chunk, dict):
            try:
                content = chunk['model']['messages'][-1].content
            except KeyError:
                content = ""     
        else:
                content = getattr(chunk, "content", "")
        return content
    
    @staticmethod 
    def get_chunk_id(chunk):
        if isinstance(chunk, dict):
            chunk_id = chunk.get("id", str(uuid4()))
        else:
            chunk_id = getattr(chunk, "id", str(uuid4()))
        return chunk_id
    
    @RunnableGenerator
    def stream_openai_response(self, chunks: Iterable[AIMessageChunk]) -> Iterable[bytes]:
        """Convert DeepAgents (or plain AIMessageChunk) output into OpenAI‑compatible SSE.

        DeepAgents may emit either ``AIMessageChunk`` objects or plain ``dict``
        structures.  We gracefully handle both by extracting ``content`` and an
        optional ``id``.  If an ``id`` is missing we generate a UUID so the client
        receives a well‑formed response.
        """
        for chunk in chunks:
            # Debug output – keep it simple to avoid leaking large data.
            # Support both object and dict representations.
            chunk_id = self.get_chunk_id(chunk)
            content = self.get_content(chunk)
            data = self.format_data(chunk_id,
                                    self.model,
                                    self.system_fingerprint,
                                    content)
            # print('\ndata', data)
            yield bytes(f"data: {data}\n\n", "utf-8")