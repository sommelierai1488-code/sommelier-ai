"""
Database operations for API
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
from .config import DB_CONFIG, DEFAULT_RECOMMENDATIONS_COUNT


def get_db_connection():
    """
    Create a database connection

    Returns:
        Connection object
    """
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def get_random_products(limit: int = DEFAULT_RECOMMENDATIONS_COUNT) -> List[Dict[str, Any]]:
    """
    Get random products from database

    Args:
        limit: Number of products to return

    Returns:
        List of product dictionaries
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get random products with available data
        # TODO: Add filtering based on quiz parameters when ML model is ready
        query = """
            SELECT
                sku,
                name,
                product_url,
                price_current,
                image_urls,
                availability_status
            FROM products
            WHERE
                availability_status = 'available'
                AND price_current IS NOT NULL
                AND name IS NOT NULL
            ORDER BY RANDOM()
            LIMIT %s
        """

        cursor.execute(query, (limit,))
        products = cursor.fetchall()

        return products

    finally:
        cursor.close()
        conn.close()


def format_product_for_response(product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format database product to API response format

    Args:
        product: Product dictionary from database

    Returns:
        Formatted product dictionary
    """
    # Extract first image URL from JSONB array
    image_url = ""
    if product.get('image_urls'):
        if isinstance(product['image_urls'], list) and len(product['image_urls']) > 0:
            image_url = product['image_urls'][0]

    # Format price
    price_raw = f"{int(product.get('price_current', 0))} ₽" if product.get('price_current') else "Цена не указана"

    return {
        "id": product.get('sku', ''),
        "description": product.get('name', 'Без названия'),
        "image": image_url,
        "url": product.get('product_url', ''),
        "price_raw": price_raw
    }
