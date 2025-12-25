-- Create cryptocurrencies table
CREATE TABLE IF NOT EXISTS cryptocurrencies (
    canonical_id VARCHAR(255) PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    current_price NUMERIC(20, 8),
    market_cap NUMERIC(30, 2),
    total_volume NUMERIC(30, 2),
    price_change_24h NUMERIC(20, 8),
    price_change_percentage_24h NUMERIC(10, 4),
    last_updated TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create source mappings table
CREATE TABLE IF NOT EXISTS source_mappings (
    id SERIAL PRIMARY KEY,
    canonical_id VARCHAR(255),
    source VARCHAR(50) NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, source_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_crypto_symbol ON cryptocurrencies(symbol);
CREATE INDEX IF NOT EXISTS idx_crypto_market_cap ON cryptocurrencies(market_cap);
CREATE INDEX IF NOT EXISTS idx_source_canonical ON source_mappings(canonical_id);
CREATE INDEX IF NOT EXISTS idx_source_lookup ON source_mappings(source, source_id);

-- Insert sample data for verification
INSERT INTO cryptocurrencies (canonical_id, symbol, name, current_price, market_cap, last_updated)
VALUES ('btc', 'BTC', 'Bitcoin', 45000.00, 900000000000.00, NOW())
ON CONFLICT (canonical_id) DO NOTHING;