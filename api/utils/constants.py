import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Tuple


class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"


class Category(str, Enum):
    WORK = "Work"
    PERSONAL = "Personal"
    FINANCE = "Finance"
    OTHER = "Other"


@dataclass
class PriorityResult:
    priority: Priority
    confidence: int
    source: str
    reasoning: Dict[str, Any] = None


class PriorityIndicator:
    def __init__(self, patterns: List[str], weight: int):
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        self.weight = weight


class PriorityInference:
    def __init__(self):
        # Priority patterns with weights
        self.high_indicators = [
            # Explicit urgency
            PriorityIndicator([
                r"urgent",
                r"asap",
                r"emergency",
                r"critical",
                r"immediate(ly)?",
                r"right away",
            ], 10),

            # Deadline indicators
            PriorityIndicator([
                r"by (today|tomorrow|tonight)",
                r"due (today|tomorrow|tonight)",
                r"within \d+ hours?",
                r"end of( the)? day",
            ], 8),

            # Important stakeholders
            PriorityIndicator([
                r"(boss|client|customer) (needs|wants|requested)",
                r"executive",
                r"CEO",
                r"board meeting",
            ], 7),

            # Financial/Legal implications
            PriorityIndicator([
                r"deadline",
                r"tax",
                r"legal",
                r"compliance",
                r"regulatory",
            ], 6)
        ]

        self.medium_indicators = [
            # Time-bound but not urgent
            PriorityIndicator([
                r"this week",
                r"next week",
                r"upcoming",
                r"soon",
                r"schedule[d]?",
            ], 5),

            # Project-related
            PriorityIndicator([
                r"project",
                r"meeting",
                r"presentation",
                r"report",
                r"review",
            ], 4),

            # Follow-up activities
            PriorityIndicator([
                r"follow[- ]?up",
                r"check[- ]?in",
                r"update",
            ], 3)
        ]

        self.low_indicators = [
            # Optional/Flexible tasks
            PriorityIndicator([
                r"when possible",
                r"if you can",
                r"would be nice",
                r"maybe",
                r"consider",
            ], 2),

            # Maintenance/Routine
            PriorityIndicator([
                r"routine",
                r"regular",
                r"maintenance",
                r"organize",
                r"clean",
            ], 1)
        ]

    def infer_priority(self, task_description: str, current_priority: str = "Unknown") -> Tuple[str, dict]:
        """
        Infer task priority with detailed reasoning.

        Returns:
            Tuple of (priority, reasoning_dict)
        """
        scores = {
            "high": 0,
            "medium": 0,
            "low": 0
        }

        matches = {
            "high": [],
            "medium": [],
            "low": []
        }

        # Check for date patterns
        due_date_match = re.search(r"due.*?(\d{4}-\d{2}-\d{2})", task_description)
        if due_date_match:
            try:
                due_date = datetime.strptime(due_date_match.group(1), "%Y-%m-%d").date()
                days_until_due = (due_date - datetime.now().date()).days

                if days_until_due <= 1:
                    scores["high"] += 8
                    matches["high"].append(f"Due within 24 hours")
                elif days_until_due <= 7:
                    scores["medium"] += 5
                    matches["medium"].append(f"Due within week")
            except ValueError:
                pass

        # Check all indicators
        for priority, indicators in [
            ("high", self.high_indicators),
            ("medium", self.medium_indicators),
            ("low", self.low_indicators)
        ]:
            for indicator in indicators:
                for pattern in indicator.patterns:
                    if found := pattern.search(task_description):
                        scores[priority] += indicator.weight
                        matches[priority].append(f"Matched: {found.group()}")

        # Consider current priority if not unknown
        if current_priority.lower() in scores:
            scores[current_priority.lower()] += 3
            matches[current_priority.lower()].append("Considering existing priority")

        # Determine final priority
        max_score = max(scores.values())
        if max_score == 0:
            final_priority = Priority.LOW
        else:
            final_priority = Priority[max(scores.items(), key=lambda x: x[1])[0].upper()]

        reasoning = {
            "scores": scores,
            "matches": matches,
            "final_score": max_score,
            "decision_factors": matches[final_priority.lower()],
        }

        return final_priority, reasoning

    def explain_priority(self, task_description: str) -> str:
        """Generate human-readable explanation of priority inference"""
        priority, reasoning = self.infer_priority(task_description)

        explanation = [f"Priority determined as {priority}:"]

        if reasoning["decision_factors"]:
            explanation.append("\nKey factors:")
            for factor in reasoning["decision_factors"]:
                explanation.append(f"- {factor}")

        explanation.append("\nScores:")
        for level, score in reasoning["scores"].items():
            explanation.append(f"- {level.title()}: {score}")

        return "\n".join(explanation)