from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.database import get_db, get_all_tasks
from api.database import store_task
from api.config import client
from api.models.schemas import TaskInput, TaskOutput, TaskUpdate
from api.services.task_service import TaskService

from api.utils.postprocess import process_parsed_task

router = APIRouter()
task_service = TaskService()


@router.post("/", response_model=TaskOutput)
async def create_task(task: TaskInput, db: AsyncSession = Depends(get_db)):
    """Create a new task"""
    return await task_service.parse_and_create_task(task, db)


@router.get("/search", response_model=List[TaskOutput])
async def search_tasks(
        query: str = Query(..., description="Natural language search query"),
        db: AsyncSession = Depends(get_db)
):
    """Search tasks using natural language"""
    results = await task_service.search_tasks(query=query, db=db)

    # Sort by confidence score (highest first)
    results.sort(key=lambda task: task.confidence_score, reverse=True)

    return results


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
