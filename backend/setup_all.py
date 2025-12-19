"""
Complete setup script - creates database, tables, and loads data
"""
import sys
from create_database import create_database, create_tables
from load_data import load_data_from_json


def main():
    """Run complete setup"""
    try:
        # Step 1: Create database
        print("=" * 60)
        print("Step 1: Creating database")
        print("=" * 60)
        create_database()

        # Step 2: Create tables
        print("\n" + "=" * 60)
        print("Step 2: Creating tables")
        print("=" * 60)
        create_tables()

        # Step 3: Load data
        print("\n" + "=" * 60)
        print("Step 3: Loading data from JSON")
        print("=" * 60)

        # Get JSON file path from command line or use default
        default_json_path = '/home/testuser/amwine_products.json'
        json_path = sys.argv[1] if len(sys.argv) > 1 else default_json_path

        load_data_from_json(json_path)

        # Success message
        print("\n" + "=" * 60)
        print("Setup completed successfully!")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Run 'python check_database.py' to view statistics")
        print("2. Connect to database using psql or any PostgreSQL client")
        print(f"   psql -U postgres -d amwine_products")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
