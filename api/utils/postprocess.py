from datetime import datetime
import holidays
import json
from json.decoder import JSONDecodeError

def get_holiday_date(holiday_name: str) -> str:
    """Resolve US federal holiday names to actual dates for the current year."""
    current_year = datetime.now().year
    us_holidays = holidays.country_holidays('US', years=current_year)
    
    for date, name in us_holidays.items():
        if holiday_name.lower() in name.lower():
            return date.strftime("%Y-%m-%d")

    return "Unknown"  # If the holiday is not recognized

def correct_due_date(due_date: str) -> str:
    """Ensures the due date is set to the current year."""
    current_year = datetime.now().year

    # Ensure "Tax Day" is correctly set to the current year's April 15
    if due_date.lower() in ["tax day", "april 15", "4/15"]:
        return f"{current_year}-04-15"

    # Check if OpenAI returned an outdated year and update it
    try:
        parsed_date = datetime.strptime(due_date, "%Y-%m-%d")
        if parsed_date.year < current_year:  # If it's an outdated year, update it
            return parsed_date.replace(year=current_year).strftime("%Y-%m-%d")
    except ValueError:
        pass  # Ignore if the format is incorrect

    return due_date  # Return as-is if no correction was needed

def process_parsed_task(response_content: str) -> dict:
    """Parses and validates the GPT response, ensuring the correct format."""
    if not response_content:
        raise ValueError("Invalid response format from OpenAI")

    try:
        parsed_task = json.loads(response_content)
    except JSONDecodeError:
        raise ValueError("OpenAI returned an invalid JSON response")

    # Correct the due date if necessary
    if "due_date" in parsed_task:
        parsed_task["due_date"] = correct_due_date(parsed_task["due_date"])

    return parsed_task
