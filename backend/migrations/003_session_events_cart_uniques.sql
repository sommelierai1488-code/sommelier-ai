-- Migration 003: enforce uniqueness for session_events and session_cart
-- Ensures idempotent upserts for impressions, reactions, and cart lines

-- Add unique constraint on session_events(session_id, sku) if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE t.relname = 'session_events'
          AND c.conname = 'session_events_session_sku_unique'
    ) THEN
        ALTER TABLE IF EXISTS session_events
        ADD CONSTRAINT session_events_session_sku_unique UNIQUE (session_id, sku);
    END IF;
END;
$$;

-- Add unique constraint on session_cart(session_id, sku) if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE t.relname = 'session_cart'
          AND c.conname = 'session_cart_session_sku_unique'
    ) THEN
        ALTER TABLE IF EXISTS session_cart
        ADD CONSTRAINT session_cart_session_sku_unique UNIQUE (session_id, sku);
    END IF;
END;
$$;
