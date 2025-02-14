
from sqlalchemy import Column, Integer, String, Date, DateTime, func, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from api.models.custom_types import Vector

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    due_date = Column(Date, nullable=True)
    priority = Column(String, nullable=True)
    category = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    confidence_score = Column(Integer, nullable=False, server_default='50')
    priority_source = Column(String, nullable=False, server_default='ai')
    embedding = Column(Vector(1536), nullable=True)
    search_vector = Column(TSVECTOR)


    __table_args__ = (
        CheckConstraint(
            'confidence_score >= 0 AND confidence_score <= 100',
            name='tasks_confidence_score_range'
        ),
        CheckConstraint(
            "priority_source IN ('ai', 'regex')",
            name='tasks_priority_source_values'
        )
    )
