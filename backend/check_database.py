"""
Script to check database content and statistics
"""
import psycopg2
from db_config import DB_CONFIG


def check_database():
    """Check database content and display statistics"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("=" * 60)
        print("Database Statistics")
        print("=" * 60)

        # Total products
        cursor.execute("SELECT COUNT(*) FROM products")
        total = cursor.fetchone()[0]
        print(f"\nTotal products: {total}")

        # Products by country
        print("\n" + "-" * 60)
        print("Products by country:")
        print("-" * 60)
        cursor.execute("""
            SELECT country, COUNT(*) as count
            FROM products
            GROUP BY country
            ORDER BY count DESC
            LIMIT 10
        """)
        for country, count in cursor.fetchall():
            print(f"{country or 'Unknown':30} {count:>5}")

        # Products by producer
        print("\n" + "-" * 60)
        print("Top 10 producers:")
        print("-" * 60)
        cursor.execute("""
            SELECT producer, COUNT(*) as count
            FROM products
            GROUP BY producer
            ORDER BY count DESC
            LIMIT 10
        """)
        for producer, count in cursor.fetchall():
            print(f"{producer or 'Unknown':30} {count:>5}")

        # Price statistics
        print("\n" + "-" * 60)
        print("Price statistics:")
        print("-" * 60)
        cursor.execute("""
            SELECT
                MIN(price_current) as min_price,
                MAX(price_current) as max_price,
                AVG(price_current) as avg_price,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_current) as median_price
            FROM products
            WHERE price_current IS NOT NULL
        """)
        min_price, max_price, avg_price, median_price = cursor.fetchone()
        print(f"Min price:    {min_price:>10.2f} руб")
        print(f"Max price:    {max_price:>10.2f} руб")
        print(f"Avg price:    {avg_price:>10.2f} руб")
        print(f"Median price: {median_price:>10.2f} руб")

        # Availability status
        print("\n" + "-" * 60)
        print("Availability status:")
        print("-" * 60)
        cursor.execute("""
            SELECT availability_status, COUNT(*) as count
            FROM products
            GROUP BY availability_status
            ORDER BY count DESC
        """)
        for status, count in cursor.fetchall():
            print(f"{status or 'Unknown':30} {count:>5}")

        # Sample products
        print("\n" + "-" * 60)
        print("Sample products (first 5):")
        print("-" * 60)
        cursor.execute("""
            SELECT sku, name, country, producer, price_current
            FROM products
            LIMIT 5
        """)
        for sku, name, country, producer, price in cursor.fetchall():
            print(f"\nSKU: {sku}")
            print(f"Name: {name}")
            print(f"Country: {country}")
            print(f"Producer: {producer}")
            print(f"Price: {price} руб")

        # Check excluded fields
        print("\n" + "-" * 60)
        print("Checking excluded fields:")
        print("-" * 60)

        # Check if raw_html exists (should not)
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'raw_html'
        """)
        if cursor.fetchone():
            print("⚠ WARNING: raw_html field exists in table!")
        else:
            print("✓ raw_html field not in table (correct)")

        # Check if texts_json contains excluded fields
        cursor.execute("""
            SELECT COUNT(*)
            FROM products
            WHERE texts_json ? 'Гастрономические сочетания'
               OR texts_json ? 'Затрудняетесь с выбором?'
        """)
        excluded_count = cursor.fetchone()[0]
        if excluded_count > 0:
            print(f"⚠ WARNING: {excluded_count} products have excluded fields in texts_json!")
        else:
            print("✓ No excluded fields in texts_json (correct)")

        print("\n" + "=" * 60)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == '__main__':
    check_database()
