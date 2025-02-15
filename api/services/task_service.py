from typing import List, Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.dbmodels import Task
from api.models.schemas import TaskOutput, TaskInput
from api.repositories.task_repository import TaskRepository
from api.repositories.vector_store import search_documents
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
            db: AsyncSession,
            query: str = None,
            threshold: float = 0.7,
            max_results: int = 3
    ) -> List[TaskOutput]:
        try:
            # Perform semantic search using Chroma
            similar_docs = search_documents(query, k=10)

            # Filter and sort documents based on similarity score
            filtered_docs = [
                (doc, score) for (doc, score) in similar_docs if score <= threshold
            ]

            # Sort by similarity score (lower is more similar)
            filtered_docs.sort(key=lambda x: x[1])

            # Take top results
            filtered_docs = filtered_docs[:max_results]

            # Extract task IDs from similar documents
            similar_task_ids = [int(doc.metadata['task_id']) for doc, _ in filtered_docs]

            # Fetch full task details from database
            if similar_task_ids:
                query = select(Task).where(Task.id.in_(similar_task_ids))
                result = await db.execute(query)
                tasks = result.scalars().all()

                # Add similarity scores to the output
                task_outputs = []
                for task in tasks:
                    task_output = TaskOutput.model_validate(task)
                    # Find the corresponding similarity score
                    matching_doc = next(
                        (score for (doc, score) in filtered_docs if int(doc.metadata['task_id']) == task.id), None)
                    task_output.similarity_score = matching_doc
                    task_outputs.append(task_output)

                return task_outputs

            # Fallback to traditional search if no semantic matches
            repository = TaskRepository(db)
            tasks = await repository.search(search_vector_query=query)
            return [TaskOutput.model_validate(task) for task in tasks]

        except Exception as e:
            print(f"Search error: {str(e)}")
            raise




