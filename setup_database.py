#!/usr/bin/env python3
"""Database setup script for Swing Sage Trading Platform."""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from rich.console import Console
from rich.panel import Panel
from dotenv import load_dotenv

console = Console()

def parse_database_url(database_url: str) -> dict:
    """Parse PostgreSQL URL into components."""
    # Handle postgresql:// URLs
    if database_url.startswith('postgresql://'):
        # Remove postgresql:// prefix
        url_part = database_url[13:]
        
        # Split user:pass@host:port/database
        if '@' in url_part:
            auth_part, host_db_part = url_part.split('@', 1)
            if ':' in auth_part:
                user, password = auth_part.split(':', 1)
            else:
                user, password = auth_part, ''
        else:
            user, password = 'postgres', ''
            host_db_part = url_part
        
        # Split host:port/database
        if '/' in host_db_part:
            host_port, database = host_db_part.rsplit('/', 1)
        else:
            host_port, database = host_db_part, 'postgres'
        
        # Split host:port
        if ':' in host_port:
            host, port = host_port.rsplit(':', 1)
            port = int(port)
        else:
            host, port = host_port, 5432
        
        return {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database
        }
    else:
        raise ValueError(f"Unsupported database URL format: {database_url}")

def create_database_if_not_exists(db_config: dict) -> bool:
    """Create the database if it doesn't exist."""
    try:
        # Connect to postgres database to create our target database
        temp_config = db_config.copy()
        target_database = temp_config['database']
        temp_config['database'] = 'postgres'  # Connect to default postgres db
        
        console.print(f"Connecting to PostgreSQL server at {db_config['host']}:{db_config['port']}")
        
        conn = psycopg2.connect(**temp_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", 
            (target_database,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            console.print(f"Creating database '{target_database}'...")
            cursor.execute(f'CREATE DATABASE "{target_database}"')
            console.print(f"Database '{target_database}' created successfully")
            created = True
        else:
            console.print(f"Database '{target_database}' already exists")
            created = True  # Change this to True - existing database is fine!
            
        cursor.close()
        conn.close()
        return created
        
    except psycopg2.Error as e:
        console.print(f"Database creation failed: {e}", style="red")
        # Check if it's just a "database already exists" error
        if "already exists" in str(e).lower():
            console.print("Continuing with existing database...", style="yellow")
            return True  # Treat as success since database exists
        return False

def run_schema_file(db_config: dict, schema_file: Path) -> bool:
    """Run the schema SQL file."""
    try:
        console.print(f"Applying schema from {schema_file}")
        
        # Read the schema file
        schema_sql = schema_file.read_text(encoding='utf-8')
        
        # Remove any database connection commands since we're connecting directly
        schema_sql = schema_sql.replace('\\c options_bot;', '')
        
        # Connect to target database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Execute the schema
        cursor.execute(schema_sql)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        console.print("Schema applied successfully")
        return True
        
    except psycopg2.Error as e:
        console.print(f"Schema application failed: {e}", style="red")
        return False
    except FileNotFoundError:
        console.print(f"Schema file not found: {schema_file}", style="red")
        return False

def test_connection(db_config: dict) -> bool:
    """Test the database connection and show MVP3 schema info."""
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Get some basic info
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM events")
        events_count = cursor.fetchone()[0]
        
        # Check if views exist
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.views 
            WHERE table_name IN ('recent_events', 'event_summary', 'session_activity')
        """)
        views_count = cursor.fetchone()[0]
        
        # Check indexes
        cursor.execute("""
            SELECT COUNT(*) FROM pg_indexes 
            WHERE tablename = 'events'
        """)
        indexes_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        console.print(Panel(
            f"**MVP3 Database Connection Test**\n\n"
            f"**PostgreSQL Version:** {version.split(',')[0]}\n"
            f"**Events Table:** ✅ Created\n"
            f"**Events Count:** {events_count}\n"
            f"**Views Created:** {views_count}/3\n"
            f"**Indexes Created:** {indexes_count}\n\n"
            f"**🎯 MVP3 Ready for Event Storage!**",
            title="MVP3 Database Status",
            style="green"
        ))
        
        return True
        
    except psycopg2.Error as e:
        console.print(f"Connection test failed: {e}", style="red")
        return False

def main():
    """Main setup function."""
    console.print(Panel(
        "🎯 SWING SAGE MVP3 - UNIFIED EVENT SYSTEM\n\n"
        "This script will:\n"
        "1. Create the database if it doesn't exist\n" 
        "2. Apply the MVP3 schema (unified events table)\n"
        "3. Test the connection and verify setup\n",
        title="MVP3 Database Setup",
        style="blue"
    ))
    
    # Load environment variables
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        console.print("DATABASE_URL not found in environment", style="red")
        console.print("Make sure you have a .env file with DATABASE_URL set")
        console.print("Example: DATABASE_URL=postgresql://postgres:password@127.0.0.1:5432/swing_sage")
        sys.exit(1)
    
    # Parse database URL
    try:
        db_config = parse_database_url(database_url)
    except ValueError as e:
        console.print(f"Invalid DATABASE_URL: {e}", style="red")
        sys.exit(1)
    
    # Show configuration
    console.print(f"Database Configuration:")
    console.print(f"   Host: {db_config['host']}")
    console.print(f"   Port: {db_config['port']}")
    console.print(f"   User: {db_config['user']}")
    console.print(f"   Database: {db_config['database']}")
    
    # Step 1: Create database
    if not create_database_if_not_exists(db_config):
        console.print("Failed to create database", style="red")
        sys.exit(1)
    
    # Step 2: Apply schema
    schema_file = Path(__file__).parent / "schema.sql"
    if not run_schema_file(db_config, schema_file):
        console.print("Failed to apply schema", style="red")
        sys.exit(1)
    
    # Step 3: Test connection
    if not test_connection(db_config):
        console.print("Connection test failed", style="red")
        sys.exit(1)
    
    console.print(Panel(
        "🎉 **MVP3 Database Setup Completed!**\n\n"
        "✅ Unified events table created\n"
        "✅ Performance indexes added\n"
        "✅ Event views configured\n"
        "✅ Ready for user-triggered memory system\n\n"
        "🚀 Start using: 'Analyze NVDA' → 'push this'",
        title="Setup Complete",
        style="green"
    ))

if __name__ == "__main__":
    main()