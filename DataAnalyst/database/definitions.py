"""Database schema definition classes."""

import json
import os
from typing import Dict, Optional


class ColumnDefinition:
    """Represents a database column definition."""

    def __init__(
        self,
        name: str,
        data_type: str,
        is_nullable: bool,
        is_primary_key: bool,
        is_foreign_key: bool,
        foreign_key_reference: str,
        comments: str
    ):
        self.name = name
        self.data_type = data_type
        self.is_nullable = is_nullable
        self.is_primary_key = is_primary_key
        self.is_foreign_key = is_foreign_key
        self.foreign_key_reference = foreign_key_reference
        self.comments = comments


class TableDefinition:
    """Represents a database table definition."""

    def __init__(
        self,
        name: str,
        columns: Dict[str, ColumnDefinition]
    ):
        self.name = name
        self._columns = columns

    def write_to_file(self, storage_location: str) -> None:
        """Save the table definition to a JSON file."""
        file_path = os.path.join(storage_location, f"{self.name}.json")
        with open(file_path, "w") as f:
            json.dump({
                "name": self.name,
                "columns": {name: vars(col) for name, col in self._columns.items()}
            }, f, indent=2)

    def get_column_by_name(self, column_name: str) -> Optional[ColumnDefinition]:
        """Retrieve a column definition by its name."""
        return self._columns.get(column_name, None)