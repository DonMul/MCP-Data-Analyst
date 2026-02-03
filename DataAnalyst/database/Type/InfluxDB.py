"""InfluxDB database implementation using InfluxQL (v1)."""

import json
from typing import Any

from DataAnalyst.config import Config
from DataAnalyst.database.BaseDatabase import BaseDatabase
from DataAnalyst.database.definitions import ColumnDefinition, TableDefinition


class InfluxDB(BaseDatabase):
    """InfluxDB implementation using InfluxQL."""

    def __init__(self):
        """Initialize InfluxDB connection."""
        try:
            from influxdb import InfluxDBClient
        except ImportError as exc:
            raise ImportError(
                "influxdb is required for InfluxDB connections. "
                "Install it with: pip install influxdb"
            ) from exc

        self.client = InfluxDBClient(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            username=Config.DB_USER or None,
            password=Config.DB_PASSWORD or None,
            database=Config.DB_NAME
        )

    def execute_query(self, query: str) -> Any:
        """Execute an InfluxQL query and return results as JSON."""
        try:
            result = self.client.query(query)
            points = []
            for measurement, rows in result.items():
                for row in rows:
                    row_with_measurement = dict(row)
                    row_with_measurement["_measurement"] = measurement[0]
                    points.append(row_with_measurement)

            return json.dumps(points, default=str)
        except Exception as exc:
            raise RuntimeError(f"Failed to execute InfluxQL query: {str(exc)}") from exc

    def build_definition(self, storage_location: str) -> None:
        """Build schema definition based on measurements and field keys."""
        try:
            measurements_result = self.client.query("SHOW MEASUREMENTS")
            measurements = [m["name"] for m in measurements_result.get_points()]

            for measurement in measurements:
                field_keys_result = self.client.query(f"SHOW FIELD KEYS FROM {measurement}")
                columns = {}
                for field in field_keys_result.get_points():
                    field_name = field.get("fieldKey")
                    field_type = field.get("fieldType", "string")
                    if field_name:
                        columns[field_name] = ColumnDefinition(
                            name=field_name,
                            data_type=field_type,
                            is_nullable=True,
                            is_primary_key=False,
                            is_foreign_key=False,
                            foreign_key_reference="",
                            comments=""
                        )

                table_info = TableDefinition(name=measurement, columns=columns)
                table_info.write_to_file(storage_location)
        except Exception as exc:
            raise RuntimeError(f"Failed to build InfluxDB schema definition: {str(exc)}") from exc

    def close(self) -> None:
        """Close the InfluxDB connection."""
        if self.client:
            self.client.close()
