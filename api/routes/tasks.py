from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.database import get_db, get_all_tasks
from api.database import store_task
from api.config import client
from api.models.schemas import TaskInput, TaskOutput

from api.utils.postprocess import process_parsed_task

router = APIRouter()


@router.post("/parse-task", response_model=TaskOutput)
async def parse_task(task: TaskInput, db: AsyncSession = Depends(get_db)):
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

        # Log token usage
        tokens_used = response.usage.total_tokens
        print(f"Tokens used: {tokens_used}")
        parsed_task = process_parsed_task(response=response, task_description=task.description)
        print(f"parsed_task: {parsed_task}")

        # Get the complete task object
        db_task = await store_task(db, parsed_task)

        # The TaskOutput model will automatically convert the SQLAlchemy model
        return TaskOutput.model_validate(db_task)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/", response_model=List[TaskOutput])
async def get_tasks(db: AsyncSession = Depends(get_db)):
    """
    Retrieves all tasks from the database asynchronously.
    """
    return await get_all_tasks(db=db)
