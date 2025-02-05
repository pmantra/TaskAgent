from datetime import datetime, timedelta
import json
from json.decoder import JSONDecodeError
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


def convert_to_valid_date(due_date_str: str) -> str:
    """
    Converts natural language dates like "Friday" into a valid ISO date (YYYY-MM-DD).
    """
    try:
        # Handle relative days like "Friday"
        if due_date_str.lower() in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            today = datetime.today()
            days_ahead = (["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"].index(
                due_date_str.lower()) - today.weekday()) % 7
            if days_ahead == 0:  # If today is the same day, schedule it for next week
                days_ahead = 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        # Try parsing a normal date
        parsed_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        return parsed_date.strftime("%Y-%m-%d")

    except ValueError:
        return "Invalid Date"


def process_parsed_task(response: ChatCompletion, task_description: str) -> dict:
    """Parses and validates the GPT response, ensuring the correct format."""
    if not response or not response.choices:
        raise ValueError("Invalid OpenAI response format")

    try:
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("OpenAI returned a response with no content")
        parsed_task = json.loads(content)
    except JSONDecodeError:
        raise ValueError("OpenAI returned an invalid JSON response")

    # Correct the due date if necessary
    if "due_date" in parsed_task and isinstance(parsed_task["due_date"], str):
        parsed_task["due_date"] = convert_to_valid_date(parsed_task["due_date"])

    # Correct priority if OpenAI failed to infer it
    if "priority" in parsed_task:
        parsed_task["priority"] = infer_priority(task_description, parsed_task["priority"])

    return parsed_task
