from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)  # Concise task name
    description = Column(String, index=True)  # Full task details
    status = Column(String, default="pending")  # Task status (pending, completed)
    due_date = Column(DateTime, nullable=True)  # Optional due date
    priority = Column(String, default="Medium")  # Low, Medium, High
    category = Column(String, nullable=True)  # Task category
    created_at = Column(DateTime, default=func.now())  # Auto-set on creation
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # Auto-update on changes
