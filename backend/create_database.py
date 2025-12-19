"""
Script to create database and tables for amwine products
"""
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from db_config import DB_CONFIG


def create_database():
    """Create the database if it doesn't exist"""
    # Connect to PostgreSQL server (default postgres database)
    conn = psycopg2.connect(
        dbname='postgres',
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port']
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Check if database exists
    cursor.execute(
        "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
        (DB_CONFIG['dbname'],)
    )
    exists = cursor.fetchone()

    if not exists:
        # Create database
        cursor.execute(
            sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(DB_CONFIG['dbname'])
            )
        )
        print(f"Database '{DB_CONFIG['dbname']}' created successfully")
    else:
        print(f"Database '{DB_CONFIG['dbname']}' already exists")

    cursor.close()
    conn.close()


def create_tables():
    """Create tables using schema.sql"""
    # Connect to the newly created database
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Read and execute schema.sql
    with open('schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    cursor.execute(schema_sql)
    conn.commit()

    print("Tables created successfully")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    try:
        print("Creating database...")
        create_database()

        print("\nCreating tables...")
        create_tables()

        print("\nDatabase setup completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        raise
