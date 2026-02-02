# MCP Tools Reference

Quick reference guide for the MCP Data Analyst tools.

## Available Tools

### 1. query_database_with_prompt

**Description**: Generate and execute SQL queries from natural language.

**Parameters**:
- `prompt` (string): Natural language description of what you want to query

**Example Usage**:
```
prompt: "Show me the top 5 products by sales"
```

**Response**:
```json
{
  "success": true,
  "query": "SELECT p.name, SUM(od.quantity * od.price) as total_sales...",
  "data": [...]
}
```

**Use Cases**:
- Exploratory data analysis
- Quick business questions
- Ad-hoc reporting
- When you don't know the exact SQL syntax

---

### 2. execute_sql_query

**Description**: Execute raw SQL queries directly.

**Parameters**:
- `query` (string): The SQL query to execute

**Example Usage**:
```
query: "SELECT COUNT(*) as total FROM users WHERE created_at > '2024-01-01'"
```

**Response**:
```json
{
  "success": true,
  "data": [{"total": 1234}]
}
```

**Use Cases**:
- Precise control over query execution
- Complex queries with specific syntax
- Testing SQL statements
- When you already know the SQL you need

---

### 3. get_database_schema

**Description**: Retrieve complete database schema information.

**Parameters**: None

**Example Usage**:
```
(no parameters needed)
```

**Response**:
```json
{
  "success": true,
  "schema": {
    "users": {
      "name": "users",
      "columns": {
        "id": {
          "name": "id",
          "data_type": "int",
          "is_primary_key": true,
          "is_foreign_key": false
        }
      }
    }
  }
}
```

**Use Cases**:
- Understanding database structure
- Discovering available tables and columns
- Finding relationships between tables
- Documentation generation

---

### 4. build_db_definition

**Description**: Rebuild the database schema cache.

**Parameters**: None

**Example Usage**:
```
(no parameters needed)
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully loaded schema for 8 tables",
  "tables": ["users", "orders", "products", ...]
}
```

**Use Cases**:
- After database schema changes
- Initial setup
- Refreshing cached information
- Troubleshooting schema-related issues

---

## Error Handling

All tools return responses in this format:

**Success**:
```json
{
  "success": true,
  "data": [...]
}
```

**Error**:
```json
{
  "success": false,
  "error": "Error message here"
}
```

## Common Patterns

### Pattern 1: Explore Schema First
```
1. build_db_definition()
2. get_database_schema()
3. query_database_with_prompt("...")
```

### Pattern 2: Direct Query Execution
```
1. execute_sql_query("SELECT * FROM table")
```

### Pattern 3: Natural Language Analysis
```
1. query_database_with_prompt("What are the trends?")
2. (Review generated SQL)
3. execute_sql_query("Modified SQL if needed")
```

## Tips

1. **Schema Cache**: Always run `build_db_definition()` after database schema changes
2. **Natural Language**: Be specific in your prompts for better SQL generation
3. **Validation**: Check the generated SQL before using results in production
4. **Performance**: Use `execute_sql_query` for repeated queries to avoid LLM overhead
5. **Relationships**: The schema includes foreign key information for JOIN queries

## Examples

### Business Questions
```
"What are our top 10 customers by revenue?"
"Show me monthly sales trends for 2024"
"Which products have never been ordered?"
"Find customers who haven't ordered in 90 days"
```

### Data Analysis
```
"Calculate the average order value by customer segment"
"Show me the distribution of orders by day of week"
"What's the conversion rate from registration to first purchase?"
```

### Data Quality
```
"Find all customers with missing email addresses"
"Show me duplicate records in the users table"
"List all orders without associated products"
```
