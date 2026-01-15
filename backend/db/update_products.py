"""
Простой скрипт для добавления/обновления товаров в БД из JSON файла
Использует upsert - если товар с таким SKU есть, обновляет его, если нет - добавляет
"""
import json
import psycopg2
from psycopg2.extras import Json
from db_config import DB_CONFIG
import sys


def clean_product_data(product):
    """Очистка данных товара от исключенных полей"""
    cleaned = product.copy()

    # Удаляем raw_html
    if 'raw_html' in cleaned:
        del cleaned['raw_html']

    # Очищаем texts_json
    if 'texts_json' in cleaned and isinstance(cleaned['texts_json'], dict):
        texts = cleaned['texts_json'].copy()
        for field in ['Гастрономические сочетания', 'Затрудняетесь с выбором?']:
            if field in texts:
                del texts[field]
        cleaned['texts_json'] = texts

    return cleaned


def update_products(json_file_path='/home/testuser/amwine_products.json'):
    """
    Добавить/обновить товары из JSON файла

    Args:
        json_file_path: Путь к JSON файлу с товарами
    """
    print(f"Загрузка данных из {json_file_path}...")

    # Читаем JSON
    with open(json_file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)

    print(f"Найдено {len(products)} товаров в JSON файле")

    # Подключаемся к БД
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # SQL для upsert (добавление или обновление)
    upsert_query = """
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

    added = 0
    updated = 0
    errors = 0

    print("Добавление/обновление товаров...")

    for i, product in enumerate(products, 1):
        try:
            # Очищаем данные
            cleaned = clean_product_data(product)

            # Подготавливаем данные
            data = {
                'sku': cleaned.get('sku'),
                'source': cleaned.get('source'),
                'product_url': cleaned.get('product_url'),
                'site_product_id': cleaned.get('site_product_id'),
                'name': cleaned.get('name'),
                'category_path': cleaned.get('category_path'),
                'brand': cleaned.get('brand'),
                'producer': cleaned.get('producer'),
                'country': cleaned.get('country'),
                'price_current': cleaned.get('price_current'),
                'price_old': cleaned.get('price_old'),
                'availability_status': cleaned.get('availability_status'),
                'volume_l': cleaned.get('volume_l'),
                'abv_percent': cleaned.get('abv_percent'),
                'rating_value': cleaned.get('rating_value'),
                'rating_count': cleaned.get('rating_count'),
                'image_urls': Json(cleaned.get('image_urls', [])),
                'listing_stats': Json(cleaned.get('listing_stats', [])),
                'attrs_json': Json(cleaned.get('attrs_json', {})),
                'attrs_norm_json': Json(cleaned.get('attrs_norm_json', {})),
                'texts_json': Json(cleaned.get('texts_json', {})),
                'new_attr_keys': Json(cleaned.get('new_attr_keys', [])),
                'dedup_key': cleaned.get('dedup_key'),
                'all_product_urls': Json(cleaned.get('all_product_urls', []))
            }

            # Выполняем upsert
            cursor.execute(upsert_query, data)

            # Коммитим каждые 100 записей
            if i % 100 == 0:
                conn.commit()
                print(f"Обработано {i}/{len(products)} товаров...")

            added += 1

        except Exception as e:
            print(f"Ошибка с товаром {product.get('sku', 'unknown')}: {e}")
            errors += 1
            conn.rollback()

    # Финальный коммит
    conn.commit()

    print("\n" + "=" * 60)
    print("Обновление завершено!")
    print(f"Обработано товаров: {added}")
    print(f"Ошибок: {errors}")
    print("=" * 60)

    cursor.close()
    conn.close()


if __name__ == '__main__':
    # Можно передать путь к JSON как аргумент
    json_path = sys.argv[1] if len(sys.argv) > 1 else '/home/testuser/amwine_products.json'

    try:
        update_products(json_path)
    except FileNotFoundError:
        print(f"❌ Файл {json_path} не найден!")
        print("Использование: python update_products.py [путь_к_json]")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
