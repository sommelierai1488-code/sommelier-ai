-- Migration 002: Schema updates
-- 1. Add cart_id PK to session_cart (replacing composite PK)
-- 2. Add action_id PK to session_feedback (replacing composite PK)
-- 3. Remove budget_total from session_quiz
-- 4. Remove anon_id from sessions

-- ============================================
-- 1. UPDATE session_cart: Add cart_id as PK
-- ============================================
ALTER TABLE session_cart DROP CONSTRAINT IF EXISTS session_cart_pkey;
ALTER TABLE session_cart ADD COLUMN cart_id SERIAL PRIMARY KEY;
-- Keep unique constraint on session_id + sku
ALTER TABLE session_cart ADD CONSTRAINT session_cart_session_sku_unique UNIQUE (session_id, sku);

-- ============================================
-- 2. UPDATE session_feedback: Add action_id as PK
-- ============================================
ALTER TABLE session_feedback DROP CONSTRAINT IF EXISTS session_feedback_pkey;
ALTER TABLE session_feedback ADD COLUMN action_id SERIAL PRIMARY KEY;
-- Keep unique constraint on session_id + sku
ALTER TABLE session_feedback ADD CONSTRAINT session_feedback_session_sku_unique UNIQUE (session_id, sku);

-- ============================================
-- 3. REMOVE budget_total from session_quiz
-- ============================================
ALTER TABLE session_quiz DROP COLUMN IF EXISTS budget_total;

-- ============================================
-- 4. REMOVE anon_id from sessions
-- ============================================
-- Drop index first
DROP INDEX IF EXISTS idx_sessions_anon_id;
-- Drop column
ALTER TABLE sessions DROP COLUMN IF EXISTS anon_id;
