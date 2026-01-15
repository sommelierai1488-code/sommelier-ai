-- Database schema for amwine products and quiz sessions
-- Complete schema including all tables

-- ============================================
-- TABLE 1: PRODUCTS
-- ============================================
DROP TABLE IF EXISTS session_events CASCADE;
DROP TABLE IF EXISTS session_cart CASCADE;
DROP TABLE IF EXISTS session_feedback CASCADE;
DROP TABLE IF EXISTS session_quiz CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS products CASCADE;

CREATE TABLE products (
    sku VARCHAR(50) PRIMARY KEY,
    source VARCHAR(100),
    product_url TEXT,
    site_product_id VARCHAR(50),
    name TEXT,
    category_path TEXT,
    brand VARCHAR(255),
    producer VARCHAR(255),
    country VARCHAR(100),
    price_current DECIMAL(10, 2),
    price_old DECIMAL(10, 2),
    availability_status VARCHAR(50),
    volume_l DECIMAL(10, 2),
    abv_percent DECIMAL(5, 2),
    rating_value DECIMAL(3, 2),
    rating_count INTEGER,
    image_urls JSONB,
    listing_stats JSONB,
    attrs_json JSONB,
    attrs_norm_json JSONB,
    texts_json JSONB,
    new_attr_keys JSONB,
    dedup_key VARCHAR(50),
    all_product_urls JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for products
CREATE INDEX idx_products_source ON products(source);
CREATE INDEX idx_products_country ON products(country);
CREATE INDEX idx_products_producer ON products(producer);
CREATE INDEX idx_products_availability ON products(availability_status);
CREATE INDEX idx_products_price ON products(price_current);
CREATE INDEX idx_products_attrs_json ON products USING GIN (attrs_json);
CREATE INDEX idx_products_texts_json ON products USING GIN (texts_json);

-- ============================================
-- TABLE 2: USERS
-- ============================================
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_created_at ON users(created_at);

COMMENT ON TABLE users IS 'Пользователи системы (или анонимные)';

-- ============================================
-- TABLE 3: SESSIONS
-- ============================================
CREATE TABLE sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    status VARCHAR(20) CHECK (status IN ('in_progress', 'completed', 'abandoned')) DEFAULT 'in_progress',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for sessions
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);

COMMENT ON TABLE sessions IS 'Проходы квиза и последующий цикл под бюджет';

-- ============================================
-- TABLE 4: SESSION_QUIZ (1:1 with sessions)
-- ============================================
CREATE TABLE session_quiz (
    session_id INTEGER PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
    occasion VARCHAR(100),
    style VARCHAR(100),
    drink_types JSONB,
    tastes JSONB,
    people_count INTEGER,
    budget_bucket VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for session_quiz
CREATE INDEX idx_session_quiz_drink_types ON session_quiz USING GIN (drink_types);
CREATE INDEX idx_session_quiz_tastes ON session_quiz USING GIN (tastes);
CREATE INDEX idx_session_quiz_budget_bucket ON session_quiz(budget_bucket);

COMMENT ON TABLE session_quiz IS 'Ответы на 6 вопросов + бюджет (1:1 с sessions)';

-- ============================================
-- TABLE 5: SESSION_FEEDBACK (N:1 to sessions and products)
-- ============================================
CREATE TABLE session_feedback (
    action_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(session_id) ON DELETE CASCADE,
    sku VARCHAR(50) REFERENCES products(sku) ON DELETE CASCADE,
    action VARCHAR(10) CHECK (action IN ('like', 'dislike')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (session_id, sku)
);

-- Indexes for session_feedback
CREATE INDEX idx_session_feedback_session_id ON session_feedback(session_id);
CREATE INDEX idx_session_feedback_sku ON session_feedback(sku);
CREATE INDEX idx_session_feedback_action ON session_feedback(action);

COMMENT ON TABLE session_feedback IS 'Лайки/дизлайки на товары в рамках сессии';

-- ============================================
-- TABLE 6: SESSION_CART (N:1 to sessions and products)
-- ============================================
CREATE TABLE session_cart (
    cart_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(session_id) ON DELETE CASCADE,
    sku VARCHAR(50) REFERENCES products(sku) ON DELETE CASCADE,
    qty INTEGER NOT NULL DEFAULT 1 CHECK (qty > 0),
    price_at_add DECIMAL(10, 2) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (session_id, sku)
);

-- Indexes for session_cart
CREATE INDEX idx_session_cart_session_id ON session_cart(session_id);
CREATE INDEX idx_session_cart_sku ON session_cart(sku);

COMMENT ON TABLE session_cart IS 'Финальная корзина сессии';

-- ============================================
-- TABLE 7: SESSION_EVENTS (Event stream of user interactions)
-- ============================================
CREATE TABLE session_events (
    action_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(session_id) ON DELETE CASCADE,
    sku VARCHAR(50) REFERENCES products(sku) ON DELETE CASCADE,
    action VARCHAR(10) CHECK (action IN ('like', 'dislike', 'none')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for session_events
CREATE INDEX idx_session_events_session_id ON session_events(session_id);
CREATE INDEX idx_session_events_sku ON session_events(sku);
CREATE INDEX idx_session_events_action ON session_events(action);
CREATE INDEX idx_session_events_created_at ON session_events(created_at);
CREATE INDEX idx_session_events_session_sku ON session_events(session_id, sku);

COMMENT ON TABLE session_events IS 'Река событий - все взаимодействия пользователя с товарами в рамках сессии';

-- ============================================
-- TRIGGERS
-- ============================================
-- Trigger to auto-update updated_at in sessions table
CREATE OR REPLACE FUNCTION update_sessions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_sessions_updated_at();
