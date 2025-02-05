from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Define request model
class TaskInput(BaseModel):
    description: str


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    name: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True


class TaskOutput(BaseModel):
    id: int
    name: str
    due_date: Optional[date]
    priority: Optional[str]
    category: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
