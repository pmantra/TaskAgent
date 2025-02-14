from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field
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
    confidence_score: int = Field(
        description="AI's confidence in task analysis (0-100)"
    )
    priority_source: str = Field(
        description="Source of priority assignment ('ai' or 'regex')"
    )
    created_at: datetime
    updated_at: datetime
    # embedding: Optional[List[float]]
    similarity_score: Optional[float] = None

    class Config:
        from_attributes = True
