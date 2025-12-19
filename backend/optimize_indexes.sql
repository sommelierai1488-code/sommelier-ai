-- Additional indexes for optimizing recommendation queries
-- Run this to improve query performance

-- Index for filtering by rating and popularity (trending products)
CREATE INDEX IF NOT EXISTS idx_products_rating_composite
ON products(rating_value DESC, rating_count DESC)
WHERE availability_status = 'in_stock' AND rating_count > 0;

-- Index for JSONB attrs filtering (color for wine recommendations)
CREATE INDEX IF NOT EXISTS idx_products_attrs_color
ON products((attrs_json->>'Цвет'))
WHERE availability_status = 'in_stock';

-- Index for JSONB attrs filtering (grape variety)
CREATE INDEX IF NOT EXISTS idx_products_attrs_grape
ON products((attrs_json->>'Сорт винограда'))
WHERE availability_status = 'in_stock';

-- Index for JSONB attrs filtering (sugar content)
CREATE INDEX IF NOT EXISTS idx_products_attrs_sugar
ON products((attrs_json->>'Содержание сахара'));

-- Composite index for ABV filtering with availability
CREATE INDEX IF NOT EXISTS idx_products_abv_availability
ON products(abv_percent, availability_status);

-- Index for price range queries with availability
CREATE INDEX IF NOT EXISTS idx_products_price_availability
ON products(price_current, availability_status)
WHERE availability_status = 'in_stock';

-- Composite index for similarity searches (country + producer)
CREATE INDEX IF NOT EXISTS idx_products_country_producer
ON products(country, producer)
WHERE availability_status = 'in_stock';

-- Index for category filtering (lowercase for case-insensitive search)
CREATE INDEX IF NOT EXISTS idx_products_category_lower
ON products(LOWER(category_path))
WHERE availability_status = 'in_stock';

-- Analyze tables to update statistics
ANALYZE products;
