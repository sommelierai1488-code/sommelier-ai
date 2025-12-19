-- Примеры SQL запросов для работы с базой данных amwine_products

-- ============================================================
-- Базовые запросы
-- ============================================================

-- Получить все товары
SELECT * FROM products LIMIT 10;

-- Получить общее количество товаров
SELECT COUNT(*) as total_products FROM products;

-- Получить товар по SKU
SELECT * FROM products WHERE sku = '51240322';


-- ============================================================
-- Фильтрация по странам и производителям
-- ============================================================

-- Все товары из России
SELECT name, producer, price_current, country
FROM products
WHERE country = 'Россия'
ORDER BY price_current;

-- Товары по конкретному производителю
SELECT name, price_current, volume_l
FROM products
WHERE producer = 'Кубань-вино';

-- Топ-10 стран по количеству товаров
SELECT country, COUNT(*) as product_count
FROM products
GROUP BY country
ORDER BY product_count DESC
LIMIT 10;


-- ============================================================
-- Работа с ценами
-- ============================================================

-- Товары в ценовом диапазоне
SELECT name, price_current, country, producer
FROM products
WHERE price_current BETWEEN 500 AND 1000
ORDER BY price_current;

-- Самые дорогие товары
SELECT name, price_current, country, producer
FROM products
ORDER BY price_current DESC
LIMIT 10;

-- Самые дешевые товары
SELECT name, price_current, country, producer
FROM products
ORDER BY price_current ASC
LIMIT 10;

-- Средняя цена по странам
SELECT country,
       COUNT(*) as count,
       AVG(price_current) as avg_price,
       MIN(price_current) as min_price,
       MAX(price_current) as max_price
FROM products
WHERE price_current IS NOT NULL
GROUP BY country
ORDER BY avg_price DESC;


-- ============================================================
-- Работа с JSONB полями
-- ============================================================

-- Поиск по атрибутам (цвет вина)
SELECT name, price_current,
       attrs_json->>'Цвет' as color,
       attrs_json->>'Содержание сахара' as sugar
FROM products
WHERE attrs_json->>'Цвет' = 'Белое'
LIMIT 10;

-- Товары с определенной крепостью
SELECT name, price_current,
       attrs_json->>'Крепость' as strength
FROM products
WHERE attrs_json->>'Крепость' LIKE '40%'
LIMIT 10;

-- Поиск по тексту в описании
SELECT name, price_current,
       texts_json->>'Описание' as description
FROM products
WHERE texts_json->>'Описание' ILIKE '%виноград%'
LIMIT 5;

-- Получить все уникальные цвета
SELECT DISTINCT attrs_json->>'Цвет' as color, COUNT(*) as count
FROM products
WHERE attrs_json ? 'Цвет'
GROUP BY attrs_json->>'Цвет'
ORDER BY count DESC;


-- ============================================================
-- Работа с объемом и крепостью
-- ============================================================

-- Товары с объемом 0.75л
SELECT name, volume_l, price_current, country
FROM products
WHERE volume_l = 0.75
ORDER BY price_current
LIMIT 10;

-- Товары по крепости
SELECT name, abv_percent, price_current
FROM products
WHERE abv_percent > 40
ORDER BY abv_percent DESC
LIMIT 10;

-- Статистика по объемам
SELECT volume_l, COUNT(*) as count
FROM products
WHERE volume_l IS NOT NULL
GROUP BY volume_l
ORDER BY count DESC;


-- ============================================================
-- Наличие товаров
-- ============================================================

-- Товары в наличии
SELECT COUNT(*) as in_stock_count
FROM products
WHERE availability_status = 'in_stock';

-- Товары не в наличии
SELECT name, price_current, availability_status
FROM products
WHERE availability_status != 'in_stock'
LIMIT 10;


-- ============================================================
-- Работа с рейтингами
-- ============================================================

-- Товары с рейтингом
SELECT name, rating_value, rating_count, price_current
FROM products
WHERE rating_value IS NOT NULL
ORDER BY rating_value DESC, rating_count DESC
LIMIT 10;

-- Средний рейтинг по производителям
SELECT producer,
       AVG(rating_value) as avg_rating,
       COUNT(*) as product_count
FROM products
WHERE rating_value IS NOT NULL
GROUP BY producer
HAVING COUNT(*) > 5
ORDER BY avg_rating DESC
LIMIT 10;


-- ============================================================
-- Топ производителей
-- ============================================================

-- Топ-10 производителей по количеству товаров
SELECT producer, COUNT(*) as product_count
FROM products
GROUP BY producer
ORDER BY product_count DESC
LIMIT 10;

-- Производители с самой высокой средней ценой
SELECT producer,
       COUNT(*) as product_count,
       AVG(price_current) as avg_price
FROM products
WHERE price_current IS NOT NULL
GROUP BY producer
HAVING COUNT(*) > 10
ORDER BY avg_price DESC
LIMIT 10;


-- ============================================================
-- Анализ цен
-- ============================================================

-- Цена за литр
SELECT name, price_current, volume_l,
       ROUND(price_current / NULLIF(volume_l, 0), 2) as price_per_liter
FROM products
WHERE volume_l > 0 AND price_current IS NOT NULL
ORDER BY price_per_liter
LIMIT 10;

-- Товары со скидкой
SELECT name, price_old, price_current,
       ROUND((price_old - price_current) / price_old * 100, 2) as discount_percent
FROM products
WHERE price_old IS NOT NULL AND price_old > price_current
ORDER BY discount_percent DESC
LIMIT 10;


-- ============================================================
-- Полнотекстовый поиск
-- ============================================================

-- Поиск по названию
SELECT name, price_current, country
FROM products
WHERE name ILIKE '%вино%'
LIMIT 10;

-- Поиск по категории
SELECT name, category_path, price_current
FROM products
WHERE category_path ILIKE '%игристое%'
LIMIT 10;


-- ============================================================
-- Проверка данных
-- ============================================================

-- Товары без изображений
SELECT COUNT(*)
FROM products
WHERE image_urls IS NULL OR jsonb_array_length(image_urls) = 0;

-- Товары без цены
SELECT COUNT(*)
FROM products
WHERE price_current IS NULL;

-- Проверка наличия исключенных полей (должно вернуть 0)
SELECT COUNT(*)
FROM products
WHERE texts_json ? 'Гастрономические сочетания'
   OR texts_json ? 'Затрудняетесь с выбором?';
