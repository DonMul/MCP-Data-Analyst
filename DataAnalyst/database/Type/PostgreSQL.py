"""PostgreSQL database implementation."""

import json
from typing import Any

import psycopg
from psycopg import Connection

from DataAnalyst.config import Config
from DataAnalyst.database.BaseDatabase import BaseDatabase
from DataAnalyst.database.definitions import ColumnDefinition, TableDefinition


class PostgreSQL(BaseDatabase):
    """PostgreSQL database implementation."""

    def __init__(self):
        """Initialize PostgreSQL connection."""
        self.connection: Connection = psycopg.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            dbname=Config.DB_NAME
        )

    def execute_query(self, query: str) -> Any:
        """Execute a SQL query and return results as JSON."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            
            # Check if this is a SELECT query
            if cursor.description is None:
                self.connection.commit()
                return json.dumps({"affected_rows": cursor.rowcount})
            
            row_headers = [desc[0] for desc in cursor.description]
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
            # Get all tables in the public schema
            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )
            tables = cursor.fetchall()

            for (table_name,) in tables:
                # Get column information
                cursor.execute(
                    "SELECT column_name, data_type, is_nullable, column_default "
                    "FROM information_schema.columns "
                    f"WHERE table_name = '{table_name}' "
                    "ORDER BY ordinal_position"
                )
                columns_info = cursor.fetchall()

                # Get primary keys
                cursor.execute(
                    "SELECT a.attname "
                    "FROM pg_index i "
                    "JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) "
                    f"WHERE i.indrelid = '{table_name}'::regclass AND i.indisprimary"
                )
                primary_keys = {row[0] for row in cursor.fetchall()}

                # Get foreign keys
                cursor.execute(
                    "SELECT kcu.column_name, ccu.table_name, ccu.column_name "
                    "FROM information_schema.table_constraints AS tc "
                    "JOIN information_schema.key_column_usage AS kcu "
                    "  ON tc.constraint_name = kcu.constraint_name "
                    "  AND tc.table_schema = kcu.table_schema "
                    "JOIN information_schema.constraint_column_usage AS ccu "
                    "  ON ccu.constraint_name = tc.constraint_name "
                    "  AND ccu.table_schema = tc.table_schema "
                    f"WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = '{table_name}'"
                )
                foreign_keys = {row[0]: f"{row[1]}.{row[2]}" for row in cursor.fetchall()}

                columns = {}
                for column in columns_info:
                    name = column[0]
                    data_type = column[1]
                    is_nullable = column[2] == 'YES'
                    is_primary_key = name in primary_keys
                    is_foreign_key = name in foreign_keys
                    foreign_key_reference = foreign_keys.get(name, "")
                    
                    column_info = ColumnDefinition(
                        name=name,
                        data_type=data_type,
                        is_nullable=is_nullable,
                        is_primary_key=is_primary_key,
                        is_foreign_key=is_foreign_key,
                        foreign_key_reference=foreign_key_reference,
                        comments=""
                    )
                    columns[name] = column_info

                table_info = TableDefinition(name=table_name, columns=columns)
                table_info.write_to_file(storage_location)
        finally:
            cursor.close()

    def close(self) -> None:
        """Close the database connection."""
        if self.connection and not self.connection.closed:
            self.connection.close()