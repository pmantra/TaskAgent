import json
import os
from openai import OpenAI
from fastapi import FastAPI, HTTPException, Depends
from openai import AuthenticationError, RateLimitError, APIError, OpenAIError
from dotenv import load_dotenv
from api.models.schemas import TaskInput
from json.decoder import JSONDecodeError

from api.utils.postprocess import process_parsed_task

app = FastAPI()

dotenv_path = os.path.join(os.path.dirname(__file__), "../.env")

# Load environment variables
load_dotenv(dotenv_path=dotenv_path)

# Get API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY is not set in environment variables!")

client = OpenAI(api_key=OPENAI_API_KEY)

@app.get("/")
def read_root():
    return {"message": "TaskAgent API is running!"}

@app.post("/parse-task")
async def parse_task(task: TaskInput):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use GPT-4o if you need higher accuracy
            max_tokens=100,
            messages=[
                {"role": "user", "content": f"""
                    Extract task details as JSON:
                    - `task_name`: Short task name.
                    - `due_date`: If a deadline is mentioned.
                    - `priority`: High, Medium, or Low (determine urgency based on words like "urgent", "ASAP", "before [date]", "immediately", or time-sensitive tasks).
                    - `category`: Work, Personal, Finance, etc.

                    Task: {task.description}

                    Rules for priority:
                    - **High**: If the task includes words like "urgent", "ASAP", "immediately", or has a strict deadline.
                    - **Medium**: If the task has a deadline but no urgency.
                    - **Low**: If it's a general task with no urgency.

                    Respond ONLY with a valid JSON object.
                    """
                }
            ]
        )

        if not response.choices or not response.choices[0].message.content:
            raise HTTPException(status_code=500, detail="Invalid response format from OpenAI")
        
        content = response.choices[0].message.content        
        parsed_task = process_parsed_task(response.choices[0].message.content)        
                
        return {"success": True, "task": parsed_task}

    except AuthenticationError as e:  # Invalid API key
        raise HTTPException(status_code=401, detail=f"OpenAI Authentication Error: {str(e)}")

    except RateLimitError as e:  # Too many requests
        raise HTTPException(status_code=429, detail=f"OpenAI Rate Limit Exceeded: {str(e)}")

    except APIError as e:  # General API errors
        raise HTTPException(status_code=502, detail=f"OpenAI API Error: {str(e)}")

    except OpenAIError as e:  # Catch-all for other OpenAI exceptions
        raise HTTPException(status_code=500, detail=f"OpenAI Exception: {str(e)}")

    except Exception as e:  # General server errors
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
