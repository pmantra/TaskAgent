from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from api.database import get_db
from api.models.schemas import TaskInput, TaskOutput, TaskUpdate
from api.services.embedding_service import EmbeddingService
from api.services.llm_service import LLMService
from api.services.task_service import TaskService

from api.utils.postprocess import process_parsed_task

router = APIRouter()

# Instantiate services
llm_service = LLMService()
embedding_service = EmbeddingService()
task_service = TaskService(llm_service=llm_service, embedding_service=embedding_service)


@router.post("/", response_model=TaskOutput)
async def create_task(task: TaskInput, db: AsyncSession = Depends(get_db)):
    """Create a new task"""
    return await task_service.parse_and_create_task(task, db)


@router.get("/search", response_model=List[TaskOutput])
async def search_tasks(
        query: str = Query(..., description="Natural language search query"),
        threshold: float = Query(0.5, ge=0, le=1.0),
        db: AsyncSession = Depends(get_db)
):
    """Search tasks with debug info"""
    print(f"\nSearch request:")
    print(f"Query: {query}")
    print(f"Threshold: {threshold}")

    try:
        results = await task_service.search_tasks(
            query=query,
            threshold=threshold,
            db=db
        )
        print(f"Found {len(results)} results")
        return results
    except Exception as e:
        print(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )


@router.get("/", response_model=List[TaskOutput])
async def get_tasks(db: AsyncSession = Depends(get_db)):
    """Get all tasks"""
    return await task_service.get_all_tasks(db)


@router.get("/{task_id}", response_model=TaskOutput)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific task by ID"""
    task = await task_service.get_task_by_id(task_id=task_id, db=db)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskOutput)
async def update_task(task_id: int, task_update: TaskUpdate, db: AsyncSession = Depends(get_db)):
    """Update a task"""
    updated_task = await task_service.update_task(task_id, task_update.dict(exclude_unset=True), db)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task


@router.delete("/{task_id}", response_model=bool)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a task"""
    deleted = await task_service.delete_task(task_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return True
