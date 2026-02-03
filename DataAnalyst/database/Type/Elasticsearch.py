"""Elasticsearch database implementation using the SQL API."""

import json
from typing import Any, Dict

from DataAnalyst.config import Config
from DataAnalyst.database.BaseDatabase import BaseDatabase
from DataAnalyst.database.definitions import ColumnDefinition, TableDefinition


class Elasticsearch(BaseDatabase):
    """Elasticsearch implementation using SQL over the SQL API."""

    def __init__(self):
        """Initialize Elasticsearch connection."""
        try:
            from elasticsearch import Elasticsearch as ESClient
        except ImportError as exc:
            raise ImportError(
                "elasticsearch is required for Elasticsearch connections. "
                "Install it with: pip install elasticsearch"
            ) from exc

        scheme = getattr(Config, "DB_SCHEME", "http")
        hosts = [{"host": Config.DB_HOST, "port": Config.DB_PORT, "scheme": scheme}]

        if Config.DB_USER and Config.DB_PASSWORD:
            self.client = ESClient(hosts, basic_auth=(Config.DB_USER, Config.DB_PASSWORD))
        else:
            self.client = ESClient(hosts)

    def execute_query(self, query: str) -> Any:
        """Execute an Elasticsearch SQL query and return results as JSON."""
        try:
            response = self.client.sql.query(body={"query": query})
            columns = [col["name"] for col in response.get("columns", [])]
            rows = response.get("rows", [])

            results = [dict(zip(columns, row)) for row in rows]
            return json.dumps(results, default=str)
        except Exception as exc:
            raise RuntimeError(f"Failed to execute Elasticsearch SQL query: {str(exc)}") from exc

    def build_definition(self, storage_location: str) -> None:
        """Build index schema definitions from mappings."""
        try:
            mappings = self.client.indices.get_mapping(index="*")

            for index_name, index_body in mappings.items():
                properties: Dict[str, Dict[str, Any]] = (
                    index_body.get("mappings", {}).get("properties", {})
                )

                columns = {}
                for field_name, field_info in properties.items():
                    field_type = field_info.get("type", "object")
                    columns[field_name] = ColumnDefinition(
                        name=field_name,
                        data_type=field_type,
                        is_nullable=True,
                        is_primary_key=False,
                        is_foreign_key=False,
                        foreign_key_reference="",
                        comments=""
                    )

                table_info = TableDefinition(name=index_name, columns=columns)
                table_info.write_to_file(storage_location)
        except Exception as exc:
            raise RuntimeError(f"Failed to build Elasticsearch schema definition: {str(exc)}") from exc

    def close(self) -> None:
        """Close the Elasticsearch connection."""
        if self.client:
            self.client.close()
