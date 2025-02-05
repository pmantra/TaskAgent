from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Define request model
class TaskInput(BaseModel):
    description: str


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
