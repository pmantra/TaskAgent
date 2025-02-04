from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from api.database import get_db, get_all_tasks
from api.database import store_task
from api.config import client
from api.models.dbmodels import Task
from api.models.schemas import TaskInput, TaskOutput

from api.utils.postprocess import process_parsed_task

router = APIRouter()


@router.post("/parse-task")
async def parse_task(task: TaskInput, db: Session = Depends(get_db)):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        max_tokens=100,
        messages=[
            {"role": "user", "content": f"""
                Extract task details as JSON:
                - `name`: Short task name.
                - `due_date`: If a deadline is mentioned.
                - `priority`: High, Medium, or Low (determine urgency based on words like "urgent", "ASAP", "before [date]", "immediately", or time-sensitive tasks).
                - `category`: Work, Personal, Finance, etc.

                Task: {task.description}

                Rules for priority:
                - **High**: If the task includes words like "urgent", "ASAP", "immediately", or has a strict deadline.
                - **Medium**: If the task has a deadline but no urgency.
                - **Low**: If it's a general task with no urgency.

                Respond ONLY with a valid JSON object.
                """
             }
        ]
    )

    parsed_task = process_parsed_task(response=response, task_description=task.description)
    store_task(db, parsed_task)

    return {"success": True, "task": parsed_task}


@router.get("/", response_model=List[TaskOutput])
async def get_tasks(db: AsyncSession = Depends(get_db)):
    """
    Retrieves all tasks from the database asynchronously.
    """
    return await get_all_tasks(db=db)
