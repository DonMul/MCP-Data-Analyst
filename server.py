"""MCP Data Analyst Server.

A Model Context Protocol (MCP) server for natural language database querying.
"""

import argparse
import json
import os
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP
from openai import OpenAI

from DataAnalyst.config import Config
from DataAnalyst.database import BaseDatabase
from DataAnalyst.database.DbTypes import DbTypes
from DataAnalyst.database.Type import MySQL, PostgreSQL

# Initialize MCP server
mcp = FastMCP("data-analyst", dependencies=["openai", "mysql-connector-python", "psycopg"])

# Global state
_database_instance: BaseDatabase | None = None
_schema_cache: Dict[str, Any] = {}


def get_db_connection() -> BaseDatabase:
    """Get or create a database connection based on configuration."""
    global _database_instance
    
    if _database_instance is not None:
        return _database_instance

    db_type = Config.get_db_type()
    
    if db_type == DbTypes.MYSQL:
        _database_instance = MySQL()
    elif db_type == DbTypes.POSTGRESQL:
        _database_instance = PostgreSQL()
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    return _database_instance


def build_instructions(schemas: Dict[str, Any]) -> str:
    """Build system instructions for the LLM based on database schema."""
    return f"""You are a SQL query generator for a {Config.DB_TYPE} database.

Given the following database schema, generate an appropriate SQL query based on the user's natural language request.

IMPORTANT: Return ONLY the SQL query without any markdown formatting, explanations, or additional text.

Available tables and columns:
{json.dumps(schemas, indent=2)}

Rules:
- Generate valid {Config.DB_TYPE} SQL syntax
- Use proper JOIN clauses when querying multiple tables
- Include appropriate WHERE clauses for filtering
- Use ORDER BY when sorting is implied
- Limit results when appropriate
- Use table aliases for clarity
"""


def generate_sql_query(prompt: str) -> str:
    """Generate SQL query from natural language using LLM."""
    client = OpenAI(api_key=Config.LLM_API_KEY, base_url=Config.LLM_API_URL)
    
    try:
        response = client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=[
                {"role": "system", "content": build_instructions(_schema_cache)},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for more consistent SQL generation
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Clean up markdown code blocks if present
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        return sql_query.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to generate SQL query: {str(e)}")


@mcp.tool()
def query_database_with_prompt(prompt: str) -> str:
    """Generate and execute a database query based on a natural language prompt.
    
    Args:
        prompt: Natural language description of the desired query
        
    Returns:
        JSON string containing query results or error message
    """
    try:
        # Generate SQL query
        sql_query = generate_sql_query(prompt)
        
        # Execute query
        db = get_db_connection()
        result = db.execute_query(sql_query)
        
        return json.dumps({
            "success": True,
            "query": sql_query,
            "data": json.loads(result)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)

def execute_sql_query(query: str) -> str:
    """Execute a raw SQL query directly on the database.
    
    Args:
        query: The SQL query to execute
        
    Returns:
        JSON string containing query results or error message
    """
    try:
        db = get_db_connection()
        result = db.execute_query(query)
        
        return json.dumps({
            "success": True,
            "data": json.loads(result)
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def get_database_schema() -> str:
    """Get the complete database schema information.
    
    Returns:
        JSON string containing all table and column definitions
    """
    if not _schema_cache:
        return json.dumps({
            "success": False,
            "error": "Schema not loaded. Please run build_db_definition first."
        }, indent=2)
    
    return json.dumps({
        "success": True,
        "schema": _schema_cache
    }, indent=2)

@mcp.tool()
def build_db_definition() -> str:
    """Build or rebuild the database schema definition.
    
    This scans the connected database and creates JSON files describing
    all tables, columns, and relationships.
    
    Returns:
        JSON string indicating success or failure
    """
    try:
        db = get_db_connection()

        # Ensure schema directory exists
        schema_dir = Config.SCHEMA_DIR
        if not os.path.exists(schema_dir):
            os.makedirs(schema_dir)

        # Remove existing schema files
        for filename in os.listdir(schema_dir):
            if filename.endswith(".json"):
                os.remove(os.path.join(schema_dir, filename))

        # Build new schema definitions
        db.build_definition(schema_dir)
        
        # Reload schema cache
        _schema_cache.clear()
        for filename in os.listdir(schema_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(schema_dir, filename)
                with open(file_path, "r") as f:
                    table_name = filename[:-5]  # Remove .json extension
                    _schema_cache[table_name] = json.load(f)

        return json.dumps({
            "success": True,
            "message": f"Successfully loaded schema for {len(_schema_cache)} tables",
            "tables": list(_schema_cache.keys())
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


def run_cli_mode():
    """Run in CLI mode for interactive SQL queries."""
    print(f"\nMCP Data Analyst - CLI Mode")
    print(f"Database: {Config.DB_TYPE} ({Config.DB_NAME})")
    print("=" * 60)
    print("Enter your prompt (or 'exit' to quit)")
    print("=" * 60)
    
    while True:
        try:
            prompt = input("Your Prompt> ").strip()
            
            if not prompt:
                continue
                
            if prompt.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            
            # Execute the query
            query = generate_sql_query(prompt)
            print(f"\nGenerated SQL Query:\n{query}\n")
            result = execute_sql_query(query)
            result_data = json.loads(result)
            
            if result_data["success"]:
                data = result_data["data"]
                if isinstance(data, list) and len(data) > 0:
                    print(f"\n✓ Query returned {len(data)} row(s)")
                    print(json.dumps(data, indent=2))
                elif isinstance(data, dict):
                    print(f"\n✓ Query executed")
                    print(json.dumps(data, indent=2))
                else:
                    print(f"\n✓ Query executed successfully")
            else:
                print(f"\n✗ Error: {result_data['error']}")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


def main():
    """Main entry point for the MCP server."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MCP Data Analyst Server")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in CLI mode for interactive SQL queries instead of MCP server mode"
    )
    args = parser.parse_args()
    
    try:
        # Validate configuration
        Config.validate()
        
        # Build initial schema
        print("Building database schema...")
        result = build_db_definition()
        result_data = json.loads(result)
        
        if result_data["success"]:
            print(f"✓ {result_data['message']}")
            print(f"  Tables: {', '.join(result_data['tables'])}")
        else:
            print(f"✗ Error: {result_data['error']}")
            return
        
        # Run in CLI mode or MCP server mode
        if args.cli:
            run_cli_mode()
        else:
            # Run the MCP server
            print(f"\nStarting MCP Data Analyst server...")
            print(f"Database: {Config.DB_TYPE} ({Config.DB_NAME})")
            print(f"LLM: {Config.LLM_MODEL}")
            mcp.run(transport="stdio")
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up database connection
        if _database_instance:
            _database_instance.close()


if __name__ == "__main__":
    main()