from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update as sql_update, delete as sql_delete
from api.models.dbmodels import Task


class TaskRepository:
    def __init__(self, db):
        self.db = db

    async def get_all(self) -> List[Task]:
        """Get all tasks"""
        result = await self.db.execute(select(Task))
        return result.scalars().all()

    async def get_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by id"""
        result = await self.db.execute(select(Task).filter(Task.id == task_id))
        return result.scalar_one_or_none()

    async def create(self, task_data: dict) -> Task:
        """Create a new task"""
        db_task = Task(**task_data)
        self.db.add(db_task)
        await self.db.commit()
        await self.db.refresh(db_task)
        return db_task

    async def update(self, task_id: int, update_data: Dict[str, Any]) -> Optional[Task]:
        """
        Update a task by id
        Returns updated task or None if task not found
        """
        # First check if task exists
        task = await self.get_by_id(task_id)
        if not task:
            return None

        # Update the task
        await self.db.execute(
            sql_update(Task)
            .where(Task.id == task_id)
            .values(**update_data)
        )
        await self.db.commit()

        # Fetch and return updated task
        return await self.get_by_id(task_id)

    async def delete(self, task_id: int) -> bool:
        """
        Delete a task by id
        Returns True if task was deleted, False if task not found
        """
        result = await self.db.execute(
            sql_delete(Task).where(Task.id == task_id)
        )
        await self.db.commit()

        # rowcount will be 0 if no task was deleted
        return result.rowcount > 0

    async def search(
            self,
            search_vector_query: Optional[str] = None,
            priority: Optional[str] = None,
            category: Optional[str] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Task]:
        """Search tasks with various filters"""
        query = select(Task)
        conditions = []

        if search_vector_query:
            conditions.append(Task.search_vector.op('@@')(search_vector_query))
        if priority:
            conditions.append(Task.priority == priority)
        if category:
            conditions.append(Task.category == category)
        if start_date:
            conditions.append(Task.due_date >= start_date)
        if end_date:
            conditions.append(Task.due_date <= end_date)

        if conditions:
            query = query.filter(*conditions)

        result = await self.db.execute(query)
        return result.scalars().all()