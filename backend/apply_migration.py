"""
Script to apply database migrations
"""
import os
import psycopg2
from db_config import DB_CONFIG


def apply_migration(migration_file):
    """Apply a single migration file"""
    try:
        # Connect to the database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Read migration file
        migration_path = os.path.join('migrations', migration_file)
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Execute migration
        print(f"Applying migration: {migration_file}")
        cursor.execute(migration_sql)
        conn.commit()

        print(f"✓ Migration {migration_file} applied successfully")

        cursor.close()
        conn.close()

        return True
    except Exception as e:
        print(f"✗ Error applying migration {migration_file}: {e}")
        if conn:
            conn.rollback()
        return False


def apply_all_migrations():
    """Apply all migrations in the migrations folder"""
    migrations_dir = 'migrations'

    # Check if migrations directory exists
    if not os.path.exists(migrations_dir):
        print(f"Migrations directory '{migrations_dir}' not found")
        return

    # Get all .sql files in migrations directory
    migration_files = sorted([
        f for f in os.listdir(migrations_dir)
        if f.endswith('.sql')
    ])

    if not migration_files:
        print("No migration files found")
        return

    print(f"Found {len(migration_files)} migration(s)")
    print("-" * 50)

    success_count = 0
    for migration_file in migration_files:
        if apply_migration(migration_file):
            success_count += 1
        print("-" * 50)

    print(f"\nCompleted: {success_count}/{len(migration_files)} migrations applied successfully")


def verify_tables():
    """Verify that all tables were created"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()

        print("\nExisting tables in database:")
        for table in tables:
            print(f"  - {table[0]}")

        # Expected tables
        expected_tables = [
            'products', 'users', 'sessions',
            'session_quiz', 'session_feedback', 'session_cart'
        ]

        existing_table_names = [t[0] for t in tables]
        missing_tables = [t for t in expected_tables if t not in existing_table_names]

        if missing_tables:
            print(f"\n⚠ Warning: Missing tables: {', '.join(missing_tables)}")
        else:
            print("\n✓ All expected tables exist")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error verifying tables: {e}")


if __name__ == '__main__':
    try:
        print("=" * 50)
        print("DATABASE MIGRATION")
        print("=" * 50)

        apply_all_migrations()

        print("\n" + "=" * 50)
        print("VERIFICATION")
        print("=" * 50)

        verify_tables()

        print("\n" + "=" * 50)
        print("Migration process completed!")
        print("=" * 50)

    except Exception as e:
        print(f"Fatal error: {e}")
        raise
