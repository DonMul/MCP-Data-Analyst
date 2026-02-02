"""Configuration module for MCP Data Analyst."""

import os
from typing import Optional

from dotenv import load_dotenv

from DataAnalyst.database.DbTypes import DbTypes

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # LLM Configuration
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_API_URL: str = os.getenv("LLM_API_URL", "https://api.openai.com/v1")

    # Database Configuration
    DB_TYPE: str = os.getenv("DB_TYPE", "mysql")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "")

    # Schema cache directory
    SCHEMA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        errors = []

        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY is required")

        if not cls.DB_NAME:
            errors.append("DB_NAME is required")

        if cls.DB_TYPE not in [DbTypes.MYSQL.value, DbTypes.POSTGRESQL.value]:
            errors.append(f"DB_TYPE must be one of: {DbTypes.MYSQL.value}, {DbTypes.POSTGRESQL.value}")

        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    @classmethod
    def get_db_type(cls) -> DbTypes:
        """Get the database type as an enum."""
        if cls.DB_TYPE == DbTypes.MYSQL.value:
            return DbTypes.MYSQL
        elif cls.DB_TYPE == DbTypes.POSTGRESQL.value:
            return DbTypes.POSTGRESQL
        else:
            raise ValueError(f"Unsupported DB_TYPE: {cls.DB_TYPE}")
