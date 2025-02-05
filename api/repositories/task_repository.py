from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update as sql_update, delete as sql_delete, func, and_

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

    async def create(self, task_data: Dict[str, Any]) -> Task:
        """Create a new task with proper date handling"""
        # Ensure due_date is a date object if provided
        if task_data.get('due_date'):
            if isinstance(task_data['due_date'], str):
                try:
                    task_data['due_date'] = datetime.strptime(
                        task_data['due_date'],
                        "%Y-%m-%d"
                    ).date()
                except ValueError:
                    task_data['due_date'] = None
            elif isinstance(task_data['due_date'], datetime):
                task_data['due_date'] = task_data['due_date'].date()

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
            search_vector_query: Optional[str] = None,  # For full-text search across name, category, priority
            priority: Optional[str] = None,  # Filter by exact priority match
            category: Optional[str] = None,  # Filter by exact category match
            start_date: Optional[datetime] = None,  # Filter tasks due after this date
            end_date: Optional[datetime] = None  # Filter tasks due before this date
    ) -> List[Task]:
        """
        Search tasks with multiple filter options.
        Examples:
        1. Full text search:
            await repo.search(search_vector_query="urgent report")
        2. Priority filter:
            await repo.search(priority="High")
        3. Category filter with date range:
            await repo.search(
                category="Work",
                start_date=datetime(2025, 2, 1),
                end_date=datetime(2025, 2, 28)
            )
        4. Combined search:
            await repo.search(
                search_vector_query="report",
                priority="High",
                start_date=datetime.now()
            )
        """
        # Start with base query
        query = select(Task)
        conditions = []

        # Add full-text search if provided
        if search_vector_query:
            # Convert query to tsquery
            ts_query = func.plainto_tsquery('english', search_vector_query)
            # Add full-text search condition
            conditions.append(Task.search_vector.op('@@')(ts_query))
            # Add ordering by rank for full-text search results
            query = query.order_by(
                func.ts_rank_cd(Task.search_vector, ts_query).desc()
            )

        # Add exact filters
        if priority:
            conditions.append(Task.priority == priority)

        if category:
            conditions.append(Task.category == category)

        # Add date range filters
        if start_date:
            conditions.append(Task.due_date >= start_date)
        if end_date:
            conditions.append(Task.due_date <= end_date)

        # Combine all conditions with AND
        if conditions:
            query = query.filter(and_(*conditions))

        # Execute query and return results
        result = await self.db.execute(query)
        return result.scalars().all()