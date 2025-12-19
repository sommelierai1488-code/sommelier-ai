"""
Script to load data from JSON file into PostgreSQL database
Excludes: raw_html, "Гастрономические сочетания", "Затрудняетесь с выбором?"
"""
import json
import psycopg2
from psycopg2.extras import Json
from db_config import DB_CONFIG
from tqdm import tqdm


def clean_product_data(product):
    """
    Clean product data by removing unwanted fields

    Args:
        product: Product dictionary from JSON

    Returns:
        Cleaned product dictionary
    """
    # Create a copy to avoid modifying the original
    cleaned = product.copy()

    # Remove raw_html field
    if 'raw_html' in cleaned:
        del cleaned['raw_html']

    # Clean texts_json by removing unwanted fields
    if 'texts_json' in cleaned and isinstance(cleaned['texts_json'], dict):
        texts = cleaned['texts_json'].copy()

        # Remove unwanted fields from texts_json
        unwanted_text_fields = [
            'Гастрономические сочетания',
            'Затрудняетесь с выбором?'
        ]

        for field in unwanted_text_fields:
            if field in texts:
                del texts[field]

        cleaned['texts_json'] = texts

    return cleaned


def insert_product(cursor, product):
    """
    Insert a single product into the database

    Args:
        cursor: Database cursor
        product: Product dictionary
    """
    cleaned_product = clean_product_data(product)

    insert_query = """
        INSERT INTO products (
            sku, source, product_url, site_product_id, name,
            category_path, brand, producer, country, price_current,
            price_old, availability_status, volume_l, abv_percent,
            rating_value, rating_count, image_urls, listing_stats,
            attrs_json, attrs_norm_json, texts_json, new_attr_keys,
            dedup_key, all_product_urls
        ) VALUES (
            %(sku)s, %(source)s, %(product_url)s, %(site_product_id)s, %(name)s,
            %(category_path)s, %(brand)s, %(producer)s, %(country)s, %(price_current)s,
            %(price_old)s, %(availability_status)s, %(volume_l)s, %(abv_percent)s,
            %(rating_value)s, %(rating_count)s, %(image_urls)s, %(listing_stats)s,
            %(attrs_json)s, %(attrs_norm_json)s, %(texts_json)s, %(new_attr_keys)s,
            %(dedup_key)s, %(all_product_urls)s
        )
        ON CONFLICT (sku) DO UPDATE SET
            source = EXCLUDED.source,
            product_url = EXCLUDED.product_url,
            site_product_id = EXCLUDED.site_product_id,
            name = EXCLUDED.name,
            category_path = EXCLUDED.category_path,
            brand = EXCLUDED.brand,
            producer = EXCLUDED.producer,
            country = EXCLUDED.country,
            price_current = EXCLUDED.price_current,
            price_old = EXCLUDED.price_old,
            availability_status = EXCLUDED.availability_status,
            volume_l = EXCLUDED.volume_l,
            abv_percent = EXCLUDED.abv_percent,
            rating_value = EXCLUDED.rating_value,
            rating_count = EXCLUDED.rating_count,
            image_urls = EXCLUDED.image_urls,
            listing_stats = EXCLUDED.listing_stats,
            attrs_json = EXCLUDED.attrs_json,
            attrs_norm_json = EXCLUDED.attrs_norm_json,
            texts_json = EXCLUDED.texts_json,
            new_attr_keys = EXCLUDED.new_attr_keys,
            dedup_key = EXCLUDED.dedup_key,
            all_product_urls = EXCLUDED.all_product_urls,
            updated_at = CURRENT_TIMESTAMP
    """

    # Convert lists and dicts to JSON for PostgreSQL
    data = {
        'sku': cleaned_product.get('sku'),
        'source': cleaned_product.get('source'),
        'product_url': cleaned_product.get('product_url'),
        'site_product_id': cleaned_product.get('site_product_id'),
        'name': cleaned_product.get('name'),
        'category_path': cleaned_product.get('category_path'),
        'brand': cleaned_product.get('brand'),
        'producer': cleaned_product.get('producer'),
        'country': cleaned_product.get('country'),
        'price_current': cleaned_product.get('price_current'),
        'price_old': cleaned_product.get('price_old'),
        'availability_status': cleaned_product.get('availability_status'),
        'volume_l': cleaned_product.get('volume_l'),
        'abv_percent': cleaned_product.get('abv_percent'),
        'rating_value': cleaned_product.get('rating_value'),
        'rating_count': cleaned_product.get('rating_count'),
        'image_urls': Json(cleaned_product.get('image_urls', [])),
        'listing_stats': Json(cleaned_product.get('listing_stats', [])),
        'attrs_json': Json(cleaned_product.get('attrs_json', {})),
        'attrs_norm_json': Json(cleaned_product.get('attrs_norm_json', {})),
        'texts_json': Json(cleaned_product.get('texts_json', {})),
        'new_attr_keys': Json(cleaned_product.get('new_attr_keys', [])),
        'dedup_key': cleaned_product.get('dedup_key'),
        'all_product_urls': Json(cleaned_product.get('all_product_urls', []))
    }

    cursor.execute(insert_query, data)


def load_data_from_json(json_file_path):
    """
    Load data from JSON file into database

    Args:
        json_file_path: Path to JSON file
    """
    print(f"Loading data from {json_file_path}...")

    # Read JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    print(f"Found {len(products)} products")

    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Insert products with progress bar
    inserted = 0
    updated = 0
    errors = 0

    try:
        for product in tqdm(products, desc="Inserting products"):
            try:
                insert_product(cursor, product)
                inserted += 1

                # Commit every 100 records
                if inserted % 100 == 0:
                    conn.commit()

            except Exception as e:
                print(f"\nError inserting product {product.get('sku', 'unknown')}: {e}")
                errors += 1
                conn.rollback()

        # Final commit
        conn.commit()

        print(f"\nData loading completed!")
        print(f"Inserted/Updated: {inserted}")
        print(f"Errors: {errors}")

    except Exception as e:
        print(f"Error during data loading: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    import sys

    # Default JSON file path
    default_json_path = '/home/testuser/amwine_products.json'

    # Allow custom path as command line argument
    json_path = sys.argv[1] if len(sys.argv) > 1 else default_json_path

    try:
        load_data_from_json(json_path)
    except Exception as e:
        print(f"Failed to load data: {e}")
        sys.exit(1)
