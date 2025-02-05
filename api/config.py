import os
from functools import lru_cache
from typing import Literal

import openai
from dotenv import load_dotenv
from pydantic.v1 import BaseSettings

dotenv_path = os.path.join(os.path.dirname(__file__), "../.env")

# Load environment variables
load_dotenv()

# Get API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY is not set in environment variables!")

# OpenAI client setup
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class Settings(BaseSettings):
    # Database settings
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "agent"
    DB_HOST: str = "taskagent-db"
    DB_NAME: str = "taskagent"
    DB_PORT: int = 5432

    # Application settings
    ENV: Literal["development", "production", "test"] = "development"
    LOG_LEVEL: str = "INFO"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Returns sync database URL for migrations"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
