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
                    {"role": "user", "content": f"""
                                Extract task details as JSON:
                                - `name`: Short task name.
                                - `due_date`: Date in YYYY-MM-DD format, or null if no date mentioned.
                                - `priority`: High, Medium, or Low (determine urgency based on words like "urgent", "ASAP", "before [date]", "immediately", or time-sensitive tasks).
                                - `category`: Work, Personal, Finance, etc.

                                Task: {description}

                                Rules:
                                - dates MUST be in YYYY-MM-DD format or null
                                - priority must be High/Medium/Low based on:
                                  * High: urgent, ASAP, immediate, strict deadline
                                  * Medium: has deadline but no urgency
                                  * Low: general task with no urgency

                                Example response:
                                {{
                                    "name": "Submit tax documents",
                                    "due_date": "2025-04-15",
                                    "priority": "High",
                                    "category": "Finance"
                                }}

                                Respond ONLY with a valid JSON object.
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