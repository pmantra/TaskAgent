from datetime import date, datetime

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# Define request model
class TaskInput(BaseModel):
    description: str


class TaskOutput(BaseModel):
    id: int
    name: str
    due_date: date
    priority: str
    category: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
