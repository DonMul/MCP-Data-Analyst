# MCP Data Analyst

A Model Context Protocol (MCP) server that enables natural language querying of SQL databases using AI. Connect your database and ask questions in plain English - the server will generate and execute SQL queries for you.

## Features

- 🤖 **Natural Language to SQL**: Ask questions in plain English, get SQL results
- 🔌 **Multiple Database Support**: MySQL, PostgreSQL, MSSQL, MongoDB, SQLite, SSAS (MDX), Elasticsearch (SQL), InfluxDB (InfluxQL)
- 📊 **Schema Auto-Discovery**: Automatically scans and caches your database schema
- 🛠️ **MCP Integration**: Works seamlessly with MCP-compatible clients
- ⚡ **Efficient**: Connection pooling and schema caching for performance
- 🔒 **Read-only by Design**: Only SELECT-style queries are executed

## Query Languages

- **SQL**: MySQL, PostgreSQL, MSSQL, SQLite, Elasticsearch (SQL API)
- **MDX**: SSAS
- **InfluxQL**: InfluxDB

## Installation

### Prerequisites

- Python 3.12 or higher
- One of: MySQL, PostgreSQL, MSSQL, MongoDB, SQLite, SSAS, Elasticsearch, or InfluxDB
- OpenAI API key (or compatible API endpoint)

### Setup

1. **Clone the repository**:
   ```bash
   cd /path/to/your/workspace
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   
   Copy the example below and create a `.env` file:
   ```env
   # LLM Configuration
   LLM_API_KEY=your-api-key-here
   LLM_MODEL=gpt-3.5-turbo
   LLM_API_URL=https://api.openai.com/v1
   
  # Database Configuration
  DB_TYPE=mysql               # mysql|postgresql|mssql|mongodb|sqlite|ssas|elasticsearch|influxdb
  DB_HOST=127.0.0.1
  DB_PORT=3306                # 5432 (PostgreSQL), 1433 (MSSQL), 27017 (MongoDB), 2383 (SSAS), 9200 (Elasticsearch), 8086 (InfluxDB)
  DB_USER=root
  DB_PASSWORD=your-password
  DB_NAME=your-database-name  # For InfluxDB: database name; for SSAS/Elasticsearch: catalog/index database name
  # SQLite only
  # DB_PATH=database.db
   ```

## Usage

### Running the MCP Server

Start the server using the standard MCP stdio transport:

```bash
python server.py
```

The server will:
1. Validate configuration
2. Connect to your database
3. Build a schema cache
4. Start listening for MCP requests

### Available MCP Tools

The server exposes 3 tools that can be called by MCP clients:

#### 1. `query_database_with_prompt`
Ask questions in natural language and get SQL results.

```python
# Example: "Show me the top 5 customers by total purchases"
{
  "success": true,
  "query": "SELECT c.name, SUM(o.total) as total_purchases FROM customers c...",
  "data": [...]
}
```

#### 2. `get_database_schema`
Retrieve the complete database schema.

```python
{
  "success": true,
  "schema": {
    "users": {
      "name": "users",
      "columns": {...}
    }
  }
}
```

#### 3. `build_db_definition`
Rebuild the schema cache from the database.

```python
{
  "success": true,
  "message": "Successfully loaded schema for 8 tables",
  "tables": ["users", "orders", "products", ...]
}
```

### Integration with MCP Clients

To use this server with an MCP client (like Claude Desktop), add it to your MCP configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "data-analyst": {
      "command": "python",
      "args": ["/path/to/mcp-data-analyst/server.py"],
      "env": {
        "LLM_API_KEY": "your-key",
        "DB_TYPE": "mysql",
        "DB_HOST": "localhost",
        "DB_NAME": "your_db"
      }
    }
  }
}
```

## Development

### Adding a New Database Type

1. Create a new file in `DataAnalyst/database/Type/` (e.g., `SQLite.py`)
2. Extend the `BaseDatabase` abstract class
3. Implement all required methods: `__init__`, `execute_query`, `build_definition`, `close`
4. Add the new type to `DbTypes` enum
5. Update `DataAnalyst/database/Type/__init__.py` to export your class
6. Update `server.py` to handle the new database type

## Examples

### Example 1: Customer Analysis
```
Query: "Show me the top 10 customers by total order value"

Generated SQL:
SELECT c.customer_name, SUM(o.total_amount) as total_value
FROM customers c
JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.customer_name
ORDER BY total_value DESC
LIMIT 10;
```

### Example 2: Product Inventory
```
Query: "Which products are low in stock (less than 10 units)?"

Generated SQL:
SELECT product_name, quantity_in_stock
FROM products
WHERE quantity_in_stock < 10
ORDER BY quantity_in_stock ASC;
```

## Contributing

Contributions are welcome! Please ensure:

1. Code follows PEP 8 style guidelines
2. All functions have type hints and docstrings
3. New database types extend `BaseDatabase`
4. Changes maintain backward compatibility

## Support

For issues, questions, or contributions, please open an issue on the repository.

---

**Built with**:
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/modelcontextprotocol/fastmcp)
- [OpenAI API](https://platform.openai.com/)
