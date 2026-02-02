#!/usr/bin/env python3
"""Setup script for MCP Data Analyst.

This script helps you set up the MCP Data Analyst server quickly.
"""

import os
import sys
from pathlib import Path


def create_env_file():
    """Create .env file from user input."""
    print("\n=== MCP Data Analyst Setup ===\n")
    
    env_file = Path(".env")
    if env_file.exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return False
    
    print("\nLLM Configuration:")
    llm_api_key = input("Enter your LLM API key: ").strip()
    llm_model = input("Enter LLM model (default: gpt-3.5-turbo): ").strip() or "gpt-3.5-turbo"
    llm_api_url = input("Enter LLM API URL (default: https://api.openai.com/v1): ").strip() or "https://api.openai.com/v1"
    
    print("\nDatabase Configuration:")
    db_type = input("Enter database type (mysql/postgresql): ").strip().lower()
    
    if db_type not in ['mysql', 'postgresql']:
        print("Error: Database type must be 'mysql' or 'postgresql'")
        return False
    
    db_host = input("Enter database host (default: 127.0.0.1): ").strip() or "127.0.0.1"
    
    if db_type == 'mysql':
        db_port = input("Enter database port (default: 3306): ").strip() or "3306"
        db_user = input("Enter database user (default: root): ").strip() or "root"
    else:
        db_port = input("Enter database port (default: 5432): ").strip() or "5432"
        db_user = input("Enter database user (default: postgres): ").strip() or "postgres"
    
    db_password = input("Enter database password: ").strip()
    db_name = input("Enter database name: ").strip()
    
    if not db_name:
        print("Error: Database name is required")
        return False
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write(f"# LLM Configuration\n")
        f.write(f"LLM_API_KEY={llm_api_key}\n")
        f.write(f"LLM_MODEL={llm_model}\n")
        f.write(f"LLM_API_URL={llm_api_url}\n")
        f.write(f"\n# Database Configuration\n")
        f.write(f"DB_TYPE={db_type}\n")
        f.write(f"DB_HOST={db_host}\n")
        f.write(f"DB_PORT={db_port}\n")
        f.write(f"DB_USER={db_user}\n")
        f.write(f"DB_PASSWORD={db_password}\n")
        f.write(f"DB_NAME={db_name}\n")
    
    print(f"\n✓ Configuration saved to {env_file}")
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\nChecking dependencies...")
    
    try:
        import dotenv
        import mcp
        import openai
        print("✓ Core dependencies installed")
    except ImportError as e:
        print(f"✗ Missing dependency: {e.name}")
        print("\nPlease run: pip install -r requirements.txt")
        return False
    
    return True


def test_connection():
    """Test database connection."""
    print("\nTesting database connection...")
    
    try:
        from DataAnalyst.config import Config
        from DataAnalyst.database.Type import MySQL, PostgreSQL
        from DataAnalyst.database.DbTypes import DbTypes
        
        Config.validate()
        
        db_type = Config.get_db_type()
        if db_type == DbTypes.MYSQL:
            db = MySQL()
        else:
            db = PostgreSQL()
        
        # Try a simple query
        result = db.execute_query("SELECT 1")
        db.close()
        
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def main():
    """Main setup function."""
    print("MCP Data Analyst Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("server.py").exists():
        print("Error: Please run this script from the mcp-data-analyst directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Test connection
    if test_connection():
        print("\n" + "=" * 50)
        print("✓ Setup complete!")
        print("\nYou can now start the server with:")
        print("  python server.py")
        print("\nOr test the connection with:")
        print("  python -c 'from DataAnalyst.config import Config; Config.validate(); print(\"Config OK\")'")
    else:
        print("\n" + "=" * 50)
        print("⚠ Setup incomplete - please check your configuration")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
