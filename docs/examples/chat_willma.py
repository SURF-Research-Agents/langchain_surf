import os
from dotenv import load_dotenv
from langchain_surf import ChatWillma

load_dotenv('../../../.env')  # Load environment variables from .env file

api_key = os.getenv("AIHUB_API_KEY")
model = "default-text-large"

model = ChatWillma(
    model=model,
    temperature=0.1,
    max_tokens=1000,
    timeout=30,
    api_key=api_key,
)

result = model.invoke("What is the capital of Paraguay?")
print(result)
