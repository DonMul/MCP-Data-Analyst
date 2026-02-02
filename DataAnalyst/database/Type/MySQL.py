"""MySQL database implementation."""

import json
from typing import Any

from mysql import connector
from mysql.connector import MySQLConnection

from DataAnalyst.config import Config
from DataAnalyst.database.BaseDatabase import BaseDatabase
from DataAnalyst.database.definitions import ColumnDefinition, TableDefinition


class MySQL(BaseDatabase):
    """MySQL database implementation."""

    def __init__(self):
        """Initialize MySQL connection."""
        self.connection: MySQLConnection = connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
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
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            for (table_name,) in tables:
                cursor.execute(f"SHOW FULL COLUMNS FROM {table_name}")
                columns_info = cursor.fetchall()

                columns = {}
                for column in columns_info:
                    name = column[0]
                    data_type = column[1]
                    is_nullable = column[3] == 'YES'
                    is_primary_key = column[4] == 'PRI'
                    is_foreign_key = column[4] == 'MUL'
                    foreign_key_reference = ""
                    comments = column[8] or ""
                    
                    column_info = ColumnDefinition(
                        name=name,
                        data_type=data_type,
                        is_nullable=is_nullable,
                        is_primary_key=is_primary_key,
                        is_foreign_key=is_foreign_key,
                        foreign_key_reference=foreign_key_reference,
                        comments=comments
                    )
                    columns[name] = column_info

                table_info = TableDefinition(name=table_name, columns=columns)
                
                # Get foreign key information
                cursor.execute(
                    f"SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, "
                    f"REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME "
                    f"FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                    f"WHERE TABLE_SCHEMA = '{Config.DB_NAME}'"
                )
                fk_info = cursor.fetchall()
                
                for fk in fk_info:
                    if fk[0] == table_name and fk[2] != 'PRIMARY':
                        col_name = fk[1]
                        if col_name in columns:
                            col = table_info.get_column_by_name(col_name)
                            if col:
                                col.is_foreign_key = True
                                col.foreign_key_reference = f"{fk[3]}.{fk[4]}"

                table_info.write_to_file(storage_location)
        finally:
            cursor.close()

    def close(self) -> None:
        """Close the database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()