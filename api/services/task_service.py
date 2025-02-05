from typing import List, Optional, Dict, Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import client
from api.models.schemas import TaskOutput, TaskInput
from api.repositories.task_repository import TaskRepository
from api.utils.postprocess import process_parsed_task


class TaskService:
    def __init__(self):
        self.client = client

    async def get_all_tasks(self, db: AsyncSession) -> list[TaskOutput]:
        repository = TaskRepository(db)
        tasks = await repository.get_all()
        return [TaskOutput.model_validate(task) for task in tasks]

    async def parse_and_create_task(self, task_input: TaskInput, db: AsyncSession) -> TaskOutput:
        repository = TaskRepository(db)
        response = self._get_openai_parsing(task_input.description)
        parsed_task = process_parsed_task(response=response, task_description=task_input.description)
        db_task = await repository.create(parsed_task)
        return TaskOutput.model_validate(db_task)

    async def get_task_by_id(self, task_id: int, db: AsyncSession) -> Optional[TaskOutput]:
        repository = TaskRepository(db)
        task = await repository.get_by_id(task_id)
        return TaskOutput.model_validate(task) if task else None

    async def update_task(self, task_id: int, update_data: Dict[str, Any], db: AsyncSession) -> Optional[TaskOutput]:
        repository = TaskRepository(db)
        updated_task = await repository.update(task_id, update_data)
        return TaskOutput.model_validate(updated_task) if updated_task else None

    async def delete_task(self, task_id: int, db: AsyncSession) -> bool:
        repository = TaskRepository(db)
        return await repository.delete(task_id)

    async def search_tasks(
            self,
            db: AsyncSession,
            query: str = None,
            filters: dict = None
    ) -> List[TaskOutput]:
        repository = TaskRepository(db)

        tasks = await repository.search(
            search_vector_query=query,
            priority=filters.get('priority'),
            category=filters.get('category'),
            start_date=filters.get('start_date'),
            end_date=filters.get('end_date')
        )

        return [TaskOutput.model_validate(task) for task in tasks]

    def _get_openai_parsing(self, description: str):
        """
        Parses a task description using OpenAI and assigns a category and due-date automatically.
        """
        try:
            response = client.chat.completions.create(
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