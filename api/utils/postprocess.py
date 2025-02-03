from datetime import datetime
import holidays
import json
from json.decoder import JSONDecodeError
from fastapi import HTTPException
from openai.types.chat import ChatCompletion


def infer_priority(task_description: str, priority: str) -> str:
    """Determines priority if OpenAI fails to infer it."""
    if priority.lower() != "unknown":
        return priority

    # Set priority based on urgency-related words in task description
    urgent_keywords = ["urgent", "asap", "immediately", "now", "important", "before"]
    medium_keywords = ["deadline", "due", "by", "submit"]

    task_lower = task_description.lower()

    if any(word in task_lower for word in urgent_keywords):
        return "High"
    elif any(word in task_lower for word in medium_keywords):
        return "Medium"
    return "Low"  # Default to Low if no urgency is found


def correct_due_date(due_date: str) -> str:
    """Ensures the due date is set to the current year."""
    current_year = datetime.now().year
    due_date_lower = due_date.lower()
    us_holidays = holidays.country_holidays('US', years=current_year)

    # Ensure "Tax Day" is correctly set to the current year's April 15
    if due_date.lower() in ["tax day", "april 15", "4/15"]:
        return f"{current_year}-04-15"

    for year in [current_year, current_year + 1]:
        for date, name in  us_holidays.items():
            if date.year == year and name.lower() == due_date_lower:
                return date.strftime("%Y-%m-%d")

    return due_date


def process_parsed_task(response: ChatCompletion, task_description: str) -> dict:
    """Parses and validates the GPT response, ensuring the correct format."""
    if not response or not response.choices:
        raise HTTPException(status_code=500, detail="Invalid response format from OpenAI")

    try:
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("OpenAI returned a response with no content")
        parsed_task = json.loads(content)
    except JSONDecodeError:
        raise ValueError("OpenAI returned an invalid JSON response")

    # Correct the due date if necessary
    if "due_date" in parsed_task:
        parsed_task["due_date"] = correct_due_date(parsed_task["due_date"])

    # Correct priority if OpenAI failed to infer it
    if "priority" in parsed_task:
        parsed_task["priority"] = infer_priority(task_description, parsed_task["priority"])

    return parsed_task
