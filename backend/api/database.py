"""
Database operations for API
"""
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import List, Dict, Any, Optional
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
                availability_status IN ('available', 'in_stock')
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


def insert_session_events_batch(session_id: int, events: List[Dict[str, str]]) -> int:
    """
    Insert multiple session events in a batch

    Args:
        session_id: Session ID
        events: List of event dictionaries with 'sku' and 'action' keys

    Returns:
        Number of inserted records

    Raises:
        Exception: If database operation fails
    """
    if not events:
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Prepare data for batch insert
        insert_query = """
            INSERT INTO session_events (session_id, sku, action)
            VALUES (%s, %s, %s)
        """

        # Create list of tuples for executemany
        values = [(session_id, event['sku'], event['action']) for event in events]

        # Execute batch insert
        cursor.executemany(insert_query, values)
        conn.commit()

        return len(values)

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


# ============================================
# SESSION MANAGEMENT FUNCTIONS
# ============================================

def create_session(user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Create a new session

    Args:
        user_id: User ID (optional, can be None for anonymous users)

    Returns:
        Dictionary with session_id, status, and created_at

    Raises:
        Exception: If database operation fails
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        insert_query = """
            INSERT INTO sessions (user_id, status)
            VALUES (%s, 'in_progress')
            RETURNING session_id, status, created_at
        """

        cursor.execute(insert_query, (user_id,))
        result = cursor.fetchone()
        conn.commit()

        return {
            "session_id": result['session_id'],
            "status": result['status'],
            "created_at": result['created_at'].isoformat()
        }

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def save_quiz_answers(
    session_id: int,
    occasion: str,
    style: str,
    drink_types: List[str],
    tastes: List[str],
    people_count: int,
    budget: str
) -> bool:
    """
    Save or update quiz answers for a session (UPSERT)

    Args:
        session_id: Session ID
        occasion: Occasion for purchase
        style: Drink style
        drink_types: List of drink types (multi-select)
        tastes: List of taste preferences (multi-select)
        people_count: Number of people
        budget: Budget bucket

    Returns:
        True if successful

    Raises:
        Exception: If database operation fails
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        upsert_query = """
            INSERT INTO session_quiz
                (session_id, occasion, style, drink_types, tastes, people_count, budget_bucket)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id)
            DO UPDATE SET
                occasion = EXCLUDED.occasion,
                style = EXCLUDED.style,
                drink_types = EXCLUDED.drink_types,
                tastes = EXCLUDED.tastes,
                people_count = EXCLUDED.people_count,
                budget_bucket = EXCLUDED.budget_bucket,
                created_at = CURRENT_TIMESTAMP
        """

        cursor.execute(
            upsert_query,
            (session_id, occasion, style, Json(drink_types), Json(tastes), people_count, budget)
        )
        conn.commit()

        # Update session updated_at
        update_session_timestamp(session_id)

        return True

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


# ============================================
# CART MANAGEMENT FUNCTIONS
# ============================================

def add_to_cart(session_id: int, sku: str, qty: int, price_at_add: float) -> bool:
    """
    Add or update item in cart (UPSERT)

    Args:
        session_id: Session ID
        sku: Product SKU
        qty: Quantity
        price_at_add: Price at the time of adding

    Returns:
        True if successful

    Raises:
        Exception: If database operation fails
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        upsert_query = """
            INSERT INTO session_cart (session_id, sku, qty, price_at_add)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (session_id, sku)
            DO UPDATE SET
                qty = EXCLUDED.qty,
                price_at_add = EXCLUDED.price_at_add,
                added_at = CURRENT_TIMESTAMP
        """

        cursor.execute(upsert_query, (session_id, sku, qty, price_at_add))
        conn.commit()

        # Update session updated_at
        update_session_timestamp(session_id)

        return True

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def get_cart(session_id: int) -> Dict[str, Any]:
    """
    Get cart for a session

    Args:
        session_id: Session ID

    Returns:
        Dictionary with session_id, items, total_items, and total_price

    Raises:
        Exception: If database operation fails
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
            SELECT sku, qty, price_at_add
            FROM session_cart
            WHERE session_id = %s
            ORDER BY added_at
        """

        cursor.execute(query, (session_id,))
        items = cursor.fetchall()

        # Calculate totals
        total_items = sum(item['qty'] for item in items)
        total_price = sum(item['qty'] * float(item['price_at_add']) for item in items)

        # Convert to proper format
        items_list = [
            {
                "sku": item['sku'],
                "qty": item['qty'],
                "price_at_add": float(item['price_at_add'])
            }
            for item in items
        ]

        return {
            "session_id": session_id,
            "items": items_list,
            "total_items": total_items,
            "total_price": total_price
        }

    finally:
        cursor.close()
        conn.close()


def remove_from_cart(session_id: int, sku: str) -> bool:
    """
    Remove item from cart

    Args:
        session_id: Session ID
        sku: Product SKU

    Returns:
        True if successful

    Raises:
        Exception: If database operation fails
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        delete_query = """
            DELETE FROM session_cart
            WHERE session_id = %s AND sku = %s
        """

        cursor.execute(delete_query, (session_id, sku))
        conn.commit()

        # Update session updated_at
        update_session_timestamp(session_id)

        return True

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def complete_session(session_id: int) -> Dict[str, Any]:
    """
    Mark session as completed

    Args:
        session_id: Session ID

    Returns:
        Dictionary with session_id and status

    Raises:
        Exception: If database operation fails
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        update_query = """
            UPDATE sessions
            SET status = 'completed'
            WHERE session_id = %s
            RETURNING session_id, status
        """

        cursor.execute(update_query, (session_id,))
        result = cursor.fetchone()
        conn.commit()

        if result:
            return {
                "session_id": result['session_id'],
                "status": result['status']
            }
        else:
            raise Exception(f"Session {session_id} not found")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def update_session_timestamp(session_id: int):
    """
    Update session's updated_at timestamp

    Args:
        session_id: Session ID
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        update_query = """
            UPDATE sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE session_id = %s
        """

        cursor.execute(update_query, (session_id,))
        conn.commit()

    except Exception as e:
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
