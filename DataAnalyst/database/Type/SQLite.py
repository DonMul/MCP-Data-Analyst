"""SQLite database implementation."""

import json
import sqlite3
from typing import Any

from DataAnalyst.config import Config
from DataAnalyst.database.BaseDatabase import BaseDatabase
from DataAnalyst.database.definitions import ColumnDefinition, TableDefinition


class SQLite(BaseDatabase):
    """SQLite database implementation."""

    def __init__(self):
        """Initialize SQLite connection."""
        db_path = getattr(Config, 'DB_PATH', 'database.db')
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row

    def execute_query(self, query: str) -> Any:
        """Execute a SQL query and return results as JSON."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            
            # Check if this is a SELECT query
            if cursor.description is None:
                self.connection.commit()
                return json.dumps({"affected_rows": cursor.rowcount})
            
            row_headers = [x[0] for x in cursor.description]
            rows = cursor.fetchall()
            json_data = []
            
            for result in rows:
                json_data.append(dict(zip(row_headers, result)))

            return json.dumps(json_data, default=str)
        finally:
            cursor.close()

    def build_definition(self, storage_location: str) -> None:
        """Build the database schema definition and save it to the specified path."""
        cursor = self.connection.cursor()
        
        try:
            # Get all tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = cursor.fetchall()

            for (table_name,) in tables:
                # Get column information
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()

                columns = {}
                for column in columns_info:
                    cid, name, data_type, is_nullable, default_value, is_primary_key = column
                    
                    column_info = ColumnDefinition(
                        name=name,
                        data_type=data_type,
                        is_nullable=not is_nullable,  # 0 means NOT NULL, 1 means nullable
                        is_primary_key=bool(is_primary_key),
                        is_foreign_key=False,
                        foreign_key_reference="",
                        comments=""
                    )
                    columns[name] = column_info

                # Get foreign key information
                cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                fk_info = cursor.fetchall()
                
                for fk in fk_info:
                    seq, table_ref, from_col, to_col, on_delete, on_update, match = fk
                    if from_col in columns:
                        col = columns[from_col]
                        col.is_foreign_key = True
                        col.foreign_key_reference = f"{table_ref}.{to_col}"

                table_info = TableDefinition(name=table_name, columns=columns)
                table_info.write_to_file(storage_location)
        finally:
            cursor.close()

    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
