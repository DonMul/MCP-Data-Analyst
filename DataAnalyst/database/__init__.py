"""
Database module for MCP Data Analyst.

Provides database connection management and schema definition handling.
"""

from .BaseDatabase import BaseDatabase
from .DbTypes import DbTypes
from .definitions import ColumnDefinition, TableDefinition

__all__ = ["BaseDatabase", "DbTypes", "ColumnDefinition", "TableDefinition"]
