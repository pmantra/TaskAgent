from datetime import datetime
from typing import List, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select

from api.config import get_settings
from api.models.dbmodels import Task
from api.models.schemas import TaskOutput

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENV == "development",
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def store_task(db: AsyncSession, parsed_task: dict) -> Task:
    """
    Stores parsed task data into the database.
    Args:
        db: AsyncSession instance
        parsed_task: Dictionary containing task data
    Returns:
        Task: The created task object
    Raises:
        ValueError: If required fields are missing
    """
    if not all(key in parsed_task for key in ["name", "priority", "category"]):
        raise ValueError("Missing required task fields")

    due_date = None
    if parsed_task.get("due_date"):
        if isinstance(parsed_task["due_date"], str):
            try:
                due_date = datetime.strptime(parsed_task["due_date"], "%Y-%m-%d").date()
            except ValueError:
                due_date = None
        else:
            due_date = parsed_task["due_date"]

    db_task = Task(
        name=parsed_task["name"],
        due_date=due_date,
        priority=parsed_task.get("priority"),
        category=parsed_task.get("category")
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    return db_task


async def get_all_tasks(db: AsyncSession) -> List[TaskOutput]:
    """
    Retrieves all tasks asynchronously from the database.
    Args:
        db: AsyncSession instance
    Returns:
        List[TaskOutput]: List of tasks converted to Pydantic models
    """
    result = await db.execute(
        select(Task).order_by(Task.due_date.asc().nulls_last())
    )
    tasks = result.scalars().all()

    return [TaskOutput.model_validate(task) for task in tasks]
