# Quick Reference - MCP Data Analyst

## 🚀 Getting Started

```bash
# Install
pip install -r requirements.txt

# Configure
python setup.py

# Run
python server.py
```

## 📁 Project Structure

```
mcp-data-analyst/
├── server.py           # MCP server entry point
├── DataAnalyst/        # Python module (optimized)
│   ├── config.py       # Centralized configuration
│   └── database/       # Database abstraction
│       ├── BaseDatabase.py
│       ├── definitions.py
│       └── Type/       # MySQL, PostgreSQL
└── database/           # Schema cache (auto-generated)
```

## 🛠️ Available MCP Tools

| Tool | Purpose |
|------|---------|
| `query_database_with_prompt` | Natural language → SQL → Results |
| `execute_sql_query` | Run raw SQL directly |
| `get_database_schema` | View database structure |
| `build_db_definition` | Rebuild schema cache |

## ⚙️ Configuration (.env)

```env
# LLM
LLM_API_KEY=your-key
LLM_MODEL=gpt-3.5-turbo
LLM_API_URL=https://api.openai.com/v1

# Database
DB_TYPE=mysql|postgresql
DB_HOST=localhost
DB_PORT=3306|5432
DB_USER=root
DB_PASSWORD=password
DB_NAME=database_name
```

## 📚 Documentation

- [README.md](README.md) - Full documentation
- [MCP_TOOLS.md](MCP_TOOLS.md) - API reference with examples
- [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md) - What changed

## ✅ What Was Optimized

1. ✅ **Module Structure** - Proper Python package with `__init__.py`
2. ✅ **Code Quality** - Fixed syntax errors, added type hints
3. ✅ **MCP Server** - Proper implementation with 4 tools
4. ✅ **Database Support** - Complete MySQL & PostgreSQL
5. ✅ **Configuration** - Centralized Config class
6. ✅ **Documentation** - Comprehensive guides
7. ✅ **Developer Tools** - Setup & test scripts

## 🔧 Common Commands

```bash
# Validate config
python -c "from DataAnalyst.config import Config; Config.validate()"

# Interactive setup
python setup.py

# Check for Python errors
python -m py_compile server.py DataAnalyst/**/*.py
```

## 📖 Example Usage

```python
# Natural language query
query_database_with_prompt("Show top 10 customers by revenue")

# Direct SQL
execute_sql_query("SELECT * FROM users WHERE active = 1")

# Get schema
get_database_schema()

# Rebuild schema after DB changes
build_db_definition()
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | `pip install -r requirements.txt` |
| Config errors | Check `.env` file, run `python setup.py` |
| DB connection | Verify credentials in `.env` |
| Schema not found | Run `build_db_definition()` |

## 📦 Dependencies

- `python-dotenv` - Environment variables
- `mcp[cli]` - Model Context Protocol
- `openai` - LLM integration
- `mysql-connector-python` - MySQL support
- `psycopg[binary]` - PostgreSQL support

---

**For detailed information, see [README.md](README.md)**
