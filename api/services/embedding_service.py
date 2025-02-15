from __future__ import annotations

import asyncio
from typing import List, Dict, Any

from fastapi import HTTPException
from langchain_core.documents import Document
from openai import OpenAI
from sqlalchemy import select, func, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.dbmodels import Task
from api.repositories.vector_store import add_document


class EmbeddingService:
    def __init__(self, model: str = "text-embedding-ada-002", vector_dimension: int = 1536):
        self.client = OpenAI()
        self.model = model
        self.vector_dimension = vector_dimension

    async def generate_embedding(self, text: str) -> List[float] | None:
        try:
            print(f"Generating embedding for text: {text}")
            response = await asyncio.to_thread(
                self.client.embeddings.create,
                input=self._prepare_text(text),
                model=self.model
            )
            embedding = response.data[0].embedding
            print(f"[DEBUG] Raw embedding length: {len(embedding)}")

            # Ensure proper format and dimension
            if len(embedding) != self.vector_dimension:
                raise ValueError(f"Expected {self.vector_dimension} dimensions, got {len(embedding)}")

            print(f"Generated embedding with {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            print(f"[Embedding Error] Failed to generate embedding: {str(e)}")
            return None

    async def save_task(
            self,
            db: AsyncSession,
            task_data: Dict[str, Any],
    ) -> Task:
        try:
            embedding_text = f"{task_data['name']} {task_data.get('description', '')}"
            print(f"[DEBUG] Generating embedding for task: {embedding_text}")

            # Generate embedding using OpenAI API
            embedding = await self.generate_embedding(embedding_text)
            print(f"[DEBUG] Generated embedding: {True if embedding else False}")

            # Create the task in the database
            db_task = Task(
                name=task_data["name"],
                due_date=task_data.get("due_date"),
                priority=task_data.get("priority"),
                category=task_data.get("category"),
                embedding=embedding
            )

            db.add(db_task)
            await db.commit()
            await db.refresh(db_task)

            # Index the task in Chroma (via LangChain)
            try:
                doc_text = f"{db_task.name} {task_data.get('description', '')}"
                doc = Document(
                    page_content=doc_text,
                    metadata={
                        "task_id": db_task.id,
                        "priority": db_task.priority,
                        "category": db_task.category,
                        "created_at": db_task.created_at.isoformat()
                    }
                )
                add_document(doc)
            except Exception as chroma_error:
                print(f"[WARNING] Failed to index task in Chroma: {chroma_error}")

            return db_task

        except Exception as e:
            print(f"[ERROR] Failed to save task: {str(e)}")
            await db.rollback()
            raise

    def _prepare_text(self, text: str) -> str:
        """Prepare text for embedding generation"""
        cleaned_text = text.strip().lower()
        return cleaned_text[:8000]

    async def _find_similar_by_embedding(
            self,
            db: AsyncSession,
            query_embedding: List[float],
            threshold: float = 0.85,
            limit: int = 5
    ) -> List[Task]:
        print(f"Query Embedding: {query_embedding[:10] if query_embedding else 'None'}")

        # Rest of the method remains the same
        if query_embedding is None:
            # Fallback if no embedding generated
            query = select(Task).order_by(Task.created_at.desc()).limit(limit)
            result = await db.execute(query)
            return list(result.scalars().all())

        try:
            query = (
                select(Task)
                .filter(Task.embedding.is_not(None))  # Ensure tasks have embeddings
                .filter(func.cosine_similarity(Task.embedding, query_embedding) > threshold)
                .order_by(func.cosine_similarity(Task.embedding, query_embedding).desc())
                .limit(limit)
            )
            result = await db.execute(query)
            similar_tasks = list(result.scalars().all())

            # If no similar tasks found, return recent tasks
            if not similar_tasks:
                fallback_query = select(Task).order_by(Task.created_at.desc()).limit(limit)
                fallback_result = await db.execute(fallback_query)
                return list(fallback_result.scalars().all())

            return similar_tasks

        except Exception as e:
            print(f"[Warning] Cosine similarity failed: {str(e)}")
            query = select(Task).order_by(Task.created_at.desc()).limit(limit)
            result = await db.execute(query)
            return list(result.scalars().all())
