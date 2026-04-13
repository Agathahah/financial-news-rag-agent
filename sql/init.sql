CREATE TABLE IF NOT EXISTS fact_articles (
    id             SERIAL PRIMARY KEY,
    source         VARCHAR(100),
    title          TEXT,
    url            TEXT UNIQUE,
    summary        TEXT,
    published_date DATE,
    language       VARCHAR(10),
    created_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_daily_trends (
    published_date          DATE PRIMARY KEY,
    total_articles          INTEGER,
    mentions_bank_indonesia INTEGER DEFAULT 0,
    mentions_bi_rate        INTEGER DEFAULT 0,
    mentions_ihsg           INTEGER DEFAULT 0,
    mentions_rupiah         INTEGER DEFAULT 0,
    mentions_inflasi        INTEGER DEFAULT 0,
    mentions_ojk            INTEGER DEFAULT 0
);

CREATE INDEX idx_articles_date   ON fact_articles(published_date);
CREATE INDEX idx_articles_source ON fact_articles(source);
