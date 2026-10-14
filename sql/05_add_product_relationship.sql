
-- ============================================================
-- PROJECT: E-Commerce Intelligence
-- MIGRATION: Add product referential integrity
-- DATABASE: PostgreSQL
-- ============================================================

BEGIN;

-- Ensure every order item references an existing product.
-- Existing records were validated before this migration.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_order_items_product'
          AND conrelid = 'public.order_items'::regclass
    ) THEN
        ALTER TABLE public.order_items
            ADD CONSTRAINT fk_order_items_product
            FOREIGN KEY (product_id)
            REFERENCES public.products (product_id);
    END IF;
END;
$$;

COMMIT;
