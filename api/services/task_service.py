from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from api.models.schemas import TaskOutput, TaskInput
from api.repositories.task_repository import TaskRepository
from api.services.embedding_service import EmbeddingService
from api.services.llm_service import LLMService
from api.utils.postprocess import process_parsed_task


class TaskService:
    def __init__(self, llm_service: LLMService, embedding_service: EmbeddingService):
        self.llm_service = llm_service
        self.embedding_service = embedding_service

    async def get_all_tasks(self, db: AsyncSession) -> list[TaskOutput]:
        repository = TaskRepository(db)
        tasks = await repository.get_all()
        return [TaskOutput.model_validate(task) for task in tasks]

    async def parse_and_create_task(self, task_input: TaskInput, db: AsyncSession) -> TaskOutput:
        """Parses, generates embedding, and creates a new task in the database."""

        # Step 1: Parse task using LLM
        response = self.llm_service.parse_task_description(task_input.description)
        parsed_task = process_parsed_task(response=response, task_description=task_input.description)

        # Step 2: Use EmbeddingService to save the task
        db_task = await self.embedding_service.save_task(db, parsed_task)

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
            query: str,
            db: AsyncSession,
            threshold: float = 0.5
    ) -> List[TaskOutput]:
        # Generate embedding using EmbeddingService
        embedding = await self.embedding_service.generate_embedding(query)

        # Use repository to search database
        repository = TaskRepository(db)
        tasks_with_scores = await repository.find_similar_by_embedding(
            embedding=embedding,
            threshold=threshold
        )

        return [
            TaskOutput(
                **{
                    **task.__dict__,
                    'similarity_score': float(score)
                }
            )
            for task, score in tasks_with_scores
        ]





