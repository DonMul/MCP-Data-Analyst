"""Microsoft SQL Server database implementation."""

import json
from typing import Any

import pyodbc

from DataAnalyst.config import Config
from DataAnalyst.database.BaseDatabase import BaseDatabase
from DataAnalyst.database.definitions import ColumnDefinition, TableDefinition


class MSSQL(BaseDatabase):
    """Microsoft SQL Server database implementation."""

    def __init__(self):
        """Initialize MSSQL connection."""
        connection_string = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={Config.DB_HOST},{Config.DB_PORT};"
            f"DATABASE={Config.DB_NAME};"
            f"UID={Config.DB_USER};"
            f"PWD={Config.DB_PASSWORD};"
            f"TrustServerCertificate=yes;"
        )
        self.connection = pyodbc.connect(connection_string)

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
            # Get all tables in the database
            cursor.execute(
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_CATALOG = ?"
            , (Config.DB_NAME,))
            tables = cursor.fetchall()

            for (table_name,) in tables:
                # Get column information
                cursor.execute(
                    "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT "
                    "FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_NAME = ? "
                    "ORDER BY ORDINAL_POSITION"
                , (table_name,))
                columns_info = cursor.fetchall()

                # Get primary keys
                cursor.execute(
                    "SELECT COLUMN_NAME "
                    "FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                    "WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1 "
                    "AND TABLE_NAME = ?"
                , (table_name,))
                primary_keys = {row[0] for row in cursor.fetchall()}

                # Get foreign keys
                cursor.execute(
                    "SELECT "
                    "    KCU.COLUMN_NAME, "
                    "    KCU2.TABLE_NAME AS REFERENCED_TABLE_NAME, "
                    "    KCU2.COLUMN_NAME AS REFERENCED_COLUMN_NAME "
                    "FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS AS RC "
                    "INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU "
                    "    ON KCU.CONSTRAINT_NAME = RC.CONSTRAINT_NAME "
                    "INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS KCU2 "
                    "    ON KCU2.CONSTRAINT_NAME = RC.UNIQUE_CONSTRAINT_NAME "
                    "WHERE KCU.TABLE_NAME = ?"
                , (table_name,))
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
        if self.connection:
            self.connection.close()
