from typing import Literal
from pydantic import BaseModel

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class OpenAIRequest(BaseModel):
    model: str
    user: str
    stream: bool
    messages: list[Message]