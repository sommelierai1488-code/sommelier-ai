-- Migration: Add session-related tables
-- Created: 2025-12-16
-- Description: Creates users, sessions, session_quiz, session_feedback, and session_cart tables

-- 1. Users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for created_at if needed for queries
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- 2. Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    anon_id VARCHAR(255),  -- для анонимных пользователей
    status VARCHAR(20) CHECK (status IN ('completed', 'abandoned')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_anon_id ON sessions(anon_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);

-- 3. Session quiz table (1:1 with sessions)
CREATE TABLE IF NOT EXISTS session_quiz (
    session_id INTEGER PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
    occasion VARCHAR(100),
    style VARCHAR(100),
    drink_type VARCHAR(100),
    taste VARCHAR(100),
    people_count INTEGER,
    budget_bucket VARCHAR(50),
    budget_total DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for filtering by quiz parameters
CREATE INDEX IF NOT EXISTS idx_session_quiz_drink_type ON session_quiz(drink_type);
CREATE INDEX IF NOT EXISTS idx_session_quiz_budget_bucket ON session_quiz(budget_bucket);

-- 4. Session feedback table (N:1 to sessions, N:1 to products)
CREATE TABLE IF NOT EXISTS session_feedback (
    session_id INTEGER REFERENCES sessions(session_id) ON DELETE CASCADE,
    sku VARCHAR(50) REFERENCES products(sku) ON DELETE CASCADE,
    action VARCHAR(10) CHECK (action IN ('like', 'dislike')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, sku)
);

-- Indexes for session_feedback
CREATE INDEX IF NOT EXISTS idx_session_feedback_session_id ON session_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_session_feedback_sku ON session_feedback(sku);
CREATE INDEX IF NOT EXISTS idx_session_feedback_action ON session_feedback(action);

-- 5. Session cart table (N:1 to sessions, N:1 to products)
CREATE TABLE IF NOT EXISTS session_cart (
    session_id INTEGER REFERENCES sessions(session_id) ON DELETE CASCADE,
    sku VARCHAR(50) REFERENCES products(sku) ON DELETE CASCADE,
    qty INTEGER NOT NULL DEFAULT 1 CHECK (qty > 0),
    price_at_add DECIMAL(10, 2) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, sku)
);

-- Indexes for session_cart
CREATE INDEX IF NOT EXISTS idx_session_cart_session_id ON session_cart(session_id);
CREATE INDEX IF NOT EXISTS idx_session_cart_sku ON session_cart(sku);

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

-- Comments for documentation
COMMENT ON TABLE users IS 'Пользователи системы (или анонимные)';
COMMENT ON TABLE sessions IS 'Проходы квиза и последующий цикл под бюджет';
COMMENT ON TABLE session_quiz IS 'Ответы на 6 вопросов + бюджет (1:1 с sessions)';
COMMENT ON TABLE session_feedback IS 'Лайки/дизлайки на товары в рамках сессии';
COMMENT ON TABLE session_cart IS 'Финальная корзина сессии';
