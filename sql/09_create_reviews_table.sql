
-- ============================================================
-- PROJECT: E-Commerce Intelligence
-- MIGRATION: Create customer reviews table
-- DATABASE: PostgreSQL
-- ============================================================

BEGIN;

-- Preserve every original review record.
-- Source review_id is not unique.

CREATE TABLE IF NOT EXISTS reviews (
    review_row_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id VARCHAR(32) NOT NULL,
    order_id VARCHAR(32) NOT NULL,
    review_score INTEGER NOT NULL,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,

    CONSTRAINT fk_reviews_order
        FOREIGN KEY (order_id)
        REFERENCES orders (order_id),

    CONSTRAINT reviews_score_range
        CHECK (review_score BETWEEN 1 AND 5)
);

CREATE INDEX IF NOT EXISTS idx_reviews_order_id
    ON reviews (order_id);

CREATE INDEX IF NOT EXISTS idx_reviews_score
    ON reviews (review_score);

COMMIT;
