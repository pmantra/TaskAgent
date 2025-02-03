import os
import openai
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "../.env")

# Load environment variables
load_dotenv()

# Get API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY is not set in environment variables!")

# OpenAI client setup
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
