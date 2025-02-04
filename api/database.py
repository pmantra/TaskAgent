from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.models.dbmodels import Task
from api.models.schemas import TaskOutput

# Database connection URL (update with your credentials)
DATABASE_URL = "postgresql+asyncpg://postgres:agent@localhost/taskagent"

# Create an asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=True)

SessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine
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


def store_task(db: Session, parsed_task: dict):
    """Stores parsed task data into the database."""
    db_task = Task(
        name=parsed_task["name"],
        due_date=parsed_task["due_date"],
        priority=parsed_task["priority"],
        category=parsed_task["category"]
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task.id


async def get_all_tasks(db: AsyncSession) -> List[TaskOutput]:
    """Retrieves all tasks asynchronously from the database and converts to Pydantic models."""
    result = await db.execute(select(Task))
    tasks = result.scalars().all()

    return [TaskOutput.model_validate(task) for task in tasks]
