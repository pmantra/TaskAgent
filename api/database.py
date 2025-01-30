from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database connection URL (update with your credentials)
DATABASE_URL = "postgresql+asyncpg://username:password@localhost/taskagent"

# Create an asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Session factory for handling DB transactions
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        yield session

