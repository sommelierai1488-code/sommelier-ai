"""
Script to optimize database with additional indexes for recommendation queries
"""
import psycopg2
from db_config import DB_CONFIG


def optimize_database():
    """Add optimized indexes for recommendation engine"""
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    indexes = [
        (
            "idx_products_rating_composite",
            """CREATE INDEX IF NOT EXISTS idx_products_rating_composite
               ON products(rating_value DESC, rating_count DESC)
               WHERE availability_status = 'in_stock' AND rating_count > 0"""
        ),
        (
            "idx_products_attrs_color",
            """CREATE INDEX IF NOT EXISTS idx_products_attrs_color
               ON products((attrs_json->>'Цвет'))
               WHERE availability_status = 'in_stock'"""
        ),
        (
            "idx_products_attrs_grape",
            """CREATE INDEX IF NOT EXISTS idx_products_attrs_grape
               ON products((attrs_json->>'Сорт винограда'))
               WHERE availability_status = 'in_stock'"""
        ),
        (
            "idx_products_attrs_sugar",
            """CREATE INDEX IF NOT EXISTS idx_products_attrs_sugar
               ON products((attrs_json->>'Содержание сахара'))"""
        ),
        (
            "idx_products_abv_availability",
            """CREATE INDEX IF NOT EXISTS idx_products_abv_availability
               ON products(abv_percent, availability_status)"""
        ),
        (
            "idx_products_price_availability",
            """CREATE INDEX IF NOT EXISTS idx_products_price_availability
               ON products(price_current, availability_status)
               WHERE availability_status = 'in_stock'"""
        ),
        (
            "idx_products_country_producer",
            """CREATE INDEX IF NOT EXISTS idx_products_country_producer
               ON products(country, producer)
               WHERE availability_status = 'in_stock'"""
        ),
        (
            "idx_products_category_lower",
            """CREATE INDEX IF NOT EXISTS idx_products_category_lower
               ON products(LOWER(category_path))
               WHERE availability_status = 'in_stock'"""
        )
    ]

    print(f"Creating {len(indexes)} indexes...")

    for index_name, index_sql in indexes:
        try:
            print(f"  Creating {index_name}...", end=" ")
            cursor.execute(index_sql)
            conn.commit()
            print("✓")
        except Exception as e:
            print(f"✗ Error: {e}")
            conn.rollback()

    # Analyze tables
    print("\nAnalyzing tables to update statistics...")
    cursor.execute("ANALYZE products")
    conn.commit()
    print("✓ Analysis complete")

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("Database optimization completed!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        optimize_database()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
