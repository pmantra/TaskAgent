from sqlalchemy import Column, Integer, String, DateTime, func, Date, Index
from sqlalchemy.dialects.postgresql import TSVECTOR

from api.models.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    due_date = Column(Date, nullable=True)
    priority = Column(String, nullable=True)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    search_vector = Column(TSVECTOR)

    # Create a GIN index for faster full-text search
    __table_args__ = (
        Index(
            'idx_task_search_vector',
            'search_vector',
            postgresql_using='gin'
        ),
    )
