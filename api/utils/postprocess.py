from datetime import datetime, timedelta
import json
from json.decoder import JSONDecodeError

from fastapi import HTTPException
from openai.types.chat import ChatCompletion
from typing import Optional, Dict, Any

from api.utils.constants import Priority, Category, PriorityResult, PriorityInference


def infer_priority(task_description: str, current_priority: str = "Unknown", ai_confidence: int = 0) -> PriorityResult:
    """
    Hybrid priority inference using AI first, fallback to regex-based analysis if necessary.

    Args:
        task_description: The task text to analyze
        current_priority: Priority assigned by AI
        ai_confidence: AI's confidence score (0-100)

    Returns:
        PriorityResult with final priority and metadata
    """
    # Case 1: Trust AI if confidence is high
    if current_priority != "Unknown" and ai_confidence >= 70:
        return PriorityResult(
            priority=Priority(current_priority),
            confidence=ai_confidence,
            source="ai"
        )

    # Case 2: Use regex-based inference as fallback
    priority_model = PriorityInference()
    inferred_priority, reasoning = priority_model.infer_priority(task_description)

    # Calculate confidence based on reasoning scores
    fallback_confidence = min(
        int((reasoning['final_score'] / 10) * 100),
        100
    )

    return PriorityResult(
        priority=inferred_priority,
        confidence=fallback_confidence,
        source="regex",
        reasoning=reasoning
    )


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


def process_parsed_task(response: ChatCompletion, task_description: str) -> Dict[str, Any]:
    """Process the OpenAI response, using its confidence score"""
    # Validation code remains the same...

    try:
        parsed_task = json.loads(response.choices[0].message.content)
    except JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in OpenAI response: {str(e)}"
        )

    # Validate required fields
    required_fields = ["name", "category", "confidence_score"]
    missing_fields = [field for field in required_fields if field not in parsed_task]
    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required fields: {', '.join(missing_fields)}"
        )

    # Validate confidence score from AI
    if not isinstance(parsed_task["confidence_score"], (int, float)):
        raise HTTPException(
            status_code=422,
            detail="Invalid confidence score format"
        )

    if not (0 <= parsed_task["confidence_score"] <= 100):
        raise HTTPException(
            status_code=422,
            detail="Confidence score must be between 0 and 100"
        )

    # Only infer priority if AI's confidence is low
    if parsed_task["confidence_score"] < 50:
        inferred_priority = infer_priority(task_description, parsed_task.get("priority", "unknown"))
        parsed_task["priority"] = inferred_priority
        # Note in the response that priority was overridden
        parsed_task["priority_source"] = "inferred"
    else:
        parsed_task["priority_source"] = "ai"

    # Handle due date parsing
    if due_date := parsed_task.get("due_date"):
        parsed_task["due_date"] = parse_due_date(due_date)

    # Clean and return
    allowed_fields = {
        "name", "due_date", "priority", "category",
        "confidence_score", "priority_source"
    }

    return {k: v for k, v in parsed_task.items() if k in allowed_fields}


def calculate_confidence_score(task: Dict[str, Any], priority: Priority, description: str) -> int:
    """Calculate confidence score based on task completeness and clarity."""
    base_scores = {
        Priority.HIGH: 90,
        Priority.MEDIUM: 70,
        Priority.LOW: 50,
        Priority.UNKNOWN: 40
    }

    score = base_scores.get(priority, 50)

    # Adjust score based on task completeness
    if task.get("due_date"):
        score += 5
    if len(description.split()) >= 3:  # More detailed description
        score += 5
    if task.get("category") in Category._value2member_map_:  # Valid category
        score += 5

    return min(score, 100)  # Cap at 100


def validate_category(category: Optional[str]) -> str:
    """Validate and normalize category."""
    if not category:
        return Category.OTHER

    normalized = category.title()
    return normalized if normalized in Category._value2member_map_ else Category.OTHER


def clean_and_validate_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and validate task data types."""
    allowed_fields = {
        "name": str,
        "due_date": (str, type(None)),
        "priority": str,
        "category": str,
        "confidence_score": int,
        "description": str
    }

    return {
        k: v for k, v in task.items()
        if k in allowed_fields and isinstance(v, allowed_fields[k])
    }


def parse_due_date(due_date: str) -> Optional[str]:
    """
    Parse and validate due date strings.
    Returns ISO format date string or None if invalid.
    """
    try:
        # Try direct ISO format parsing
        return datetime.strptime(due_date, "%Y-%m-%d").date().isoformat()
    except ValueError:
        # Handle relative dates
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

        day_lower = due_date.lower()
        if day_lower in weekdays:
            today = datetime.today()
            target_weekday = weekdays[day_lower]
            days_ahead = (target_weekday - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7  # Move to next week
            return (today + timedelta(days=days_ahead)).date().isoformat()

        return None