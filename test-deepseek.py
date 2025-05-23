from crewai import LLM  # Import LLM explicitly
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

deepseek_reasoner_r1 = LLM(
    model=os.getenv("OPENROUTER_MODEL_NAME"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

print(deepseek_reasoner_r1.call(messages=[{"role": "user", "content": "Razona 1+1"}]))
