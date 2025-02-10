from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.schemas import TaskOutput, TaskInput
from api.repositories.task_repository import TaskRepository
from api.services.llm_service import LLMService
from api.utils.postprocess import process_parsed_task


class TaskService:
    def __init__(self):
        self.llm_service = LLMService()

    async def get_all_tasks(self, db: AsyncSession) -> list[TaskOutput]:
        repository = TaskRepository(db)
        tasks = await repository.get_all()
        return [TaskOutput.model_validate(task) for task in tasks]

    async def parse_and_create_task(self, task_input: TaskInput, db: AsyncSession) -> TaskOutput:
        repository = TaskRepository(db)
        response = self.llm_service.parse_task_description(task_input.description)
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
    ) -> List[TaskOutput]:
        """Search tasks using LLM for query parsing"""
        try:
            cleaned_query = query.replace('"', '').strip()
            search_params = self.llm_service.parse_search_query(cleaned_query)

            # Only pass search_terms if they're not just priority-related
            search_terms = search_params.get('search_terms', '').lower()
            if all(term in ['high', 'medium', 'low', 'priority', 'finance', 'work', 'personal']
                   for term in search_terms.split()):
                search_terms = None

            repository = TaskRepository(db)
            tasks = await repository.search(
                search_vector_query=search_terms,
                priority=search_params.get("priority"),
                category=search_params.get("category"),
            )
            return [TaskOutput.model_validate(task) for task in tasks]
        except Exception as e:
            print(f"Search error: {str(e)}")  # Debug log
            raise




