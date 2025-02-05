from datetime import datetime, timedelta
import json
from json.decoder import JSONDecodeError
from openai.types.chat import ChatCompletion
from typing import Optional


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


def convert_to_valid_date(due_date_str: str) -> Optional[datetime]:
    """
    Converts natural language dates like "Friday" into a datetime object.
    Returns None if the date is invalid.
    """
    try:
        # Handle relative days like "Friday"
        if due_date_str.lower() in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            today = datetime.today()
            days_ahead = (["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"].index(
                due_date_str.lower()) - today.weekday()) % 7
            if days_ahead == 0:  # If today is the same day, schedule it for next week
                days_ahead = 7
            return today + timedelta(days=days_ahead)

        # Try parsing a normal date
        return datetime.strptime(due_date_str, "%Y-%m-%d")

    except ValueError:
        return None


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

    # Handle due date conversion
    due_date = None
    if "due_date" in parsed_task and parsed_task["due_date"]:
        date_obj = convert_to_valid_date(parsed_task["due_date"])
        if date_obj:
            due_date = date_obj.date()  # Convert to date object for database

    # Correct priority if OpenAI failed to infer it
    if "priority" in parsed_task:
        parsed_task["priority"] = infer_priority(task_description, parsed_task["priority"])

    # Construct final task data
    return {
        "name": parsed_task.get("name", task_description),
        "due_date": due_date,  # Now returns a proper date object or None
        "priority": parsed_task.get("priority"),
        "category": parsed_task.get("category")
    }
