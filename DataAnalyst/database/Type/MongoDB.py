"""MongoDB NoSQL database implementation."""

import json
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase

from DataAnalyst.config import Config
from DataAnalyst.database.BaseDatabase import BaseDatabase
from DataAnalyst.database.definitions import ColumnDefinition, TableDefinition


class MongoDB(BaseDatabase):
    """MongoDB NoSQL database implementation."""

    def __init__(self):
        """Initialize MongoDB connection."""
        # Build connection string
        if Config.DB_USER and Config.DB_PASSWORD:
            connection_string = (
                f"mongodb://{Config.DB_USER}:{Config.DB_PASSWORD}@"
                f"{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
            )
        else:
            connection_string = f"mongodb://{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}"
        
        self.client = MongoClient(connection_string)
        self.database: MongoDatabase = self.client[Config.DB_NAME]

    def execute_query(self, query: str) -> Any:
        """Execute a MongoDB query and return results as JSON.
        
        Query format should be: collection_name.operation(args)
        Examples:
        - users.find({})
        - users.find({"age": {"$gt": 18}})
        - users.aggregate([{"$group": {"_id": "$city", "count": {"$sum": 1}}}])
        - users.count_documents({})
        """
        try:
            # Parse the query string
            # Format: collection_name.operation(json_args)
            if '.' not in query:
                raise ValueError("Query must be in format: collection_name.operation(args)")
            
            collection_name, operation_part = query.split('.', 1)
            collection = self.database[collection_name]
            
            # Extract operation and arguments
            if '(' not in operation_part:
                raise ValueError("Query must include operation with parentheses")
            
            operation = operation_part[:operation_part.index('(')]
            args_str = operation_part[operation_part.index('(')+1:operation_part.rindex(')')]
            
            # Parse arguments (safely evaluate JSON)
            if args_str.strip():
                args = json.loads(args_str) if args_str.strip() else {}
            else:
                args = {}
            
            # Execute the operation
            if operation == 'find':
                if isinstance(args, dict):
                    results = list(collection.find(args))
                else:
                    results = list(collection.find())
            elif operation == 'find_one':
                if isinstance(args, dict):
                    results = [collection.find_one(args)]
                else:
                    results = [collection.find_one()]
            elif operation == 'count_documents':
                if isinstance(args, dict):
                    count = collection.count_documents(args)
                else:
                    count = collection.count_documents({})
                results = [{"count": count}]
            elif operation == 'aggregate':
                if isinstance(args, list):
                    results = list(collection.aggregate(args))
                else:
                    raise ValueError("aggregate requires a list of pipeline stages")
            elif operation == 'distinct':
                # args should be field name
                results = collection.distinct(args if isinstance(args, str) else args.get('field', ''))
                results = [{"values": results}]
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            # Convert ObjectId to string for JSON serialization
            def convert_objectid(obj):
                if hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
                    if isinstance(obj, dict):
                        return {k: convert_objectid(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_objectid(item) for item in obj]
                return str(obj) if hasattr(obj, '__class__') and obj.__class__.__name__ == 'ObjectId' else obj
            
            results = convert_objectid(results)
            return json.dumps(results, default=str)
            
        except Exception as e:
            raise RuntimeError(f"Failed to execute MongoDB query: {str(e)}")

    def build_definition(self, storage_location: str) -> None:
        """Build the database schema definition by sampling documents."""
        try:
            # Get all collection names
            collection_names = self.database.list_collection_names()
            
            for collection_name in collection_names:
                collection = self.database[collection_name]
                
                # Sample documents to infer schema
                sample_docs = list(collection.find().limit(100))
                
                if not sample_docs:
                    continue
                
                # Analyze fields across all sampled documents
                all_fields = {}
                for doc in sample_docs:
                    for field, value in doc.items():
                        if field not in all_fields:
                            all_fields[field] = {
                                'types': set(),
                                'nullable': False,
                                'is_id': field == '_id'
                            }
                        
                        if value is None:
                            all_fields[field]['nullable'] = True
                        else:
                            all_fields[field]['types'].add(type(value).__name__)
                
                # Build column definitions
                columns = {}
                for field, info in all_fields.items():
                    data_type = ', '.join(sorted(info['types'])) if info['types'] else 'mixed'
                    
                    column_info = ColumnDefinition(
                        name=field,
                        data_type=data_type,
                        is_nullable=info['nullable'],
                        is_primary_key=info['is_id'],
                        is_foreign_key=False,
                        foreign_key_reference="",
                        comments=f"Inferred from {len(sample_docs)} sample documents"
                    )
                    columns[field] = column_info
                
                table_info = TableDefinition(name=collection_name, columns=columns)
                table_info.write_to_file(storage_location)
                
        except Exception as e:
            raise RuntimeError(f"Failed to build MongoDB schema definition: {str(e)}")

    def close(self) -> None:
        """Close the database connection."""
        if self.client:
            self.client.close()
