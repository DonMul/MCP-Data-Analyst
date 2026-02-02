"""Base class for database connections."""

from abc import ABC, abstractmethod
from typing import Any


class BaseDatabase(ABC):
    """Abstract base class for database implementations."""

    @abstractmethod
    def __init__(self):
        """Initialize the database connection."""
        pass

    @abstractmethod
    def execute_query(self, query: str) -> Any:
        """Execute a SQL query and return the results."""
        pass

    @abstractmethod
    def build_definition(self, path: str) -> None:
        """Build the database schema definition and save it to the specified path."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        pass