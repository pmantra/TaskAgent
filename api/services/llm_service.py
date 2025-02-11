import json
from typing import Dict, Any

from fastapi import HTTPException
from openai import OpenAI


class LLMService:
    def __init__(self):
        self.client = OpenAI()

    def parse_search_query(self, query: str) -> Dict[str, Any]:
        """Use OpenAI to parse natural language query into search parameters"""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=100,
            messages=[
                {"role": "system", "content": """
                            Extract search parameters from natural language queries about tasks.
                            Return a JSON object with these fields:
                            - search_terms: key words for searching (remove words like "show", "me", "all", "tasks")
                            - priority: "High"/"Medium"/"Low" if mentioned
                            - category: "Work"/"Personal"/"Finance" if mentioned

                            Examples:
                            "show me all high priority tasks"
                            {
                                "search_terms": "high priority",
                                "priority": "High",
                                "category": null
                            }

                            "find tax documents in finance category"
                            {
                                "search_terms": "tax documents",
                                "priority": null,
                                "category": "Finance"
                            }
                            """
                 },
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )

        # Log token usage
        tokens_used = response.usage.total_tokens
        print(f"Tokens used: {tokens_used}")
        result = json.loads(response.choices[0].message.content)
        print(f"LLM parsed result: {result}")  # Debug log
        return result

    def parse_task_description(self, description: str):
        """
        Parses a task description using OpenAI and assigns a category and due-date automatically.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=100,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a task management assistant that analyzes tasks and provides structured data.
                        You must always return a confidence_score (0-100) indicating your certainty in the analysis.
                        
                        Confidence Score Guidelines:
                        - 90-100: Very clear task with explicit deadline and priority indicators
                        - 70-89:  Clear task with some explicit indicators
                        - 50-69:  Basic task with implicit indicators
                        - 0-49:   Ambiguous task with minimal context
                        """
                    },
                    {
                        "role": "user",
                        "content": f"""
                Extract structured data from this task description. Return a JSON object with:

                - name: Short, clear task name
                - due_date: Date in YYYY-MM-DD format, or null if not specified
                - priority: Based on these rules:
                    * High: Contains "urgent", "ASAP", "immediately", "before [date]"
                    * Medium: Has deadline but no urgency
                    * Low: No time sensitivity
                - category: Work/Personal/Finance/Other
                - confidence_score: Your certainty (0-100) based on:
                    * Clarity of task description
                    * Presence of explicit deadline
                    * Clear priority indicators
                    * Category clarity

                Example response:
                {{
                    "name": "Submit tax documents",
                    "due_date": "2025-04-15",
                    "priority": "High",
                    "category": "Finance",
                    "confidence_score": 95
                }}

                Task Description: {description}
                """
                    }
                ]

            )

            # Log token usage
            tokens_used = response.usage.total_tokens
            print(f"Tokens used: {tokens_used}")
            return response

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
