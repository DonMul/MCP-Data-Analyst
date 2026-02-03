"""SQL Server Analysis Services (SSAS) implementation with MDX support."""

import json
from typing import Any

from DataAnalyst.config import Config
from DataAnalyst.database.BaseDatabase import BaseDatabase
from DataAnalyst.database.definitions import ColumnDefinition, TableDefinition


class SSAS(BaseDatabase):
    """SQL Server Analysis Services (SSAS) database implementation.
    
    Supports MDX (Multidimensional Expressions) queries for OLAP data analysis.
    """

    def __init__(self):
        """Initialize SSAS connection."""
        try:
            import pyodbc
        except ImportError:
            raise ImportError(
                "pyodbc is required for SSAS connections. "
                "Install it with: pip install pyodbc"
            )
        
        self.pyodbc = pyodbc
        
        # Build connection string for SSAS
        connection_string = (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server={Config.DB_HOST}:{getattr(Config, 'DB_PORT', 2383)};"
            f"Database={Config.DB_NAME};"
            f"UID={Config.DB_USER};"
            f"PWD={Config.DB_PASSWORD};"
        )
        
        try:
            self.connection = pyodbc.connect(connection_string)
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to SSAS at {Config.DB_HOST}: {str(e)}"
            )

    def execute_query(self, query: str) -> Any:
        """Execute an MDX query and return results as JSON.
        
        Args:
            query: MDX (Multidimensional Expressions) query
            
        Returns:
            JSON string containing query results
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            
            # Fetch results
            row_headers = [x[0] for x in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            json_data = []
            
            for result in rows:
                json_data.append(dict(zip(row_headers, result)))

            return json.dumps(json_data, default=str)
        finally:
            cursor.close()

    def build_definition(self, storage_location: str) -> None:
        """Build the SSAS schema definition by analyzing cubes and dimensions.
        
        SSAS uses a dimensional model rather than traditional relational tables,
        so this method documents available cubes, measures, and dimensions.
        
        Args:
            storage_location: Path to save schema definition files
        """
        cursor = self.connection.cursor()
        
        try:
            # Query system schema rowsets for SSAS metadata
            # This uses DMV (Dynamic Management Views) to get cube information
            discovery_query = """
            SELECT DISTINCT
                CATALOG_NAME,
                CUBE_NAME,
                CUBE_TYPE,
                LAST_PROCESSED
            FROM $System.MDSCHEMA_CUBES
            ORDER BY CATALOG_NAME, CUBE_NAME
            """
            
            cursor.execute(discovery_query)
            cubes = cursor.fetchall()
            
            for cube_row in cubes:
                catalog_name, cube_name, cube_type, last_processed = cube_row
                
                # Get dimensions for this cube
                dimensions_query = f"""
                SELECT DISTINCT
                    DIMENSION_NAME,
                    DIMENSION_UNIQUE_NAME,
                    DIMENSION_TYPE
                FROM $System.MDSCHEMA_DIMENSIONS
                WHERE CUBE_NAME = '{cube_name}'
                ORDER BY DIMENSION_NAME
                """
                
                cursor.execute(dimensions_query)
                dimensions = cursor.fetchall()
                
                # Get measures for this cube
                measures_query = f"""
                SELECT DISTINCT
                    MEASURE_NAME,
                    MEASURE_UNIQUE_NAME,
                    DATA_TYPE
                FROM $System.MDSCHEMA_MEASURES
                WHERE CUBE_NAME = '{cube_name}'
                ORDER BY MEASURE_NAME
                """
                
                cursor.execute(measures_query)
                measures = cursor.fetchall()
                
                # Build schema definition for this cube
                columns = {}
                
                # Add dimensions as columns
                for dim_row in dimensions:
                    dim_name = dim_row[0]
                    dim_unique_name = dim_row[1]
                    dim_type = dim_row[2] or "Standard"
                    
                    column_info = ColumnDefinition(
                        name=dim_name,
                        data_type=f"Dimension ({dim_type})",
                        is_nullable=True,
                        is_primary_key=False,
                        is_foreign_key=False,
                        foreign_key_reference="",
                        comments=f"Dimension: {dim_unique_name}"
                    )
                    columns[dim_name] = column_info
                
                # Add measures as columns
                for measure_row in measures:
                    measure_name = measure_row[0]
                    measure_unique_name = measure_row[1]
                    data_type = measure_row[2] or "Decimal"
                    
                    column_info = ColumnDefinition(
                        name=measure_name,
                        data_type=f"Measure ({data_type})",
                        is_nullable=True,
                        is_primary_key=False,
                        is_foreign_key=False,
                        foreign_key_reference="",
                        comments=f"Measure: {measure_unique_name}"
                    )
                    columns[measure_name] = column_info
                
                # Create and save table definition for this cube
                table_info = TableDefinition(name=cube_name, columns=columns)
                table_info.write_to_file(storage_location)
        
        except Exception as e:
            raise RuntimeError(f"Failed to build SSAS schema definition: {str(e)}")
        finally:
            cursor.close()

    def close(self) -> None:
        """Close the SSAS connection."""
        if self.connection:
            self.connection.close()
