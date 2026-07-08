import os
from langchain_surf import ChatWillma   
from dotenv import load_dotenv

load_dotenv('/Users/renau001/Documents/projects/ai/SRA/.env')  # Load environment variables from .env file

api_key = os.getenv("AIHUB_API_KEY")
# model = "Llama 3.1 8B Instruct"
model = "default-text-large"

model = ChatWillma(
    model=model,
    temperature=0.1,
    max_tokens=1000,
    timeout=30,
    api_key=api_key,
)

result = model.invoke("What is the capital of France?")
print(result)
