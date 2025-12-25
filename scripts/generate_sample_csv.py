import pandas as pd
from pathlib import Path

# Sample cryptocurrency data
data = {
    'id': ['bitcoin', 'ethereum', 'cardano', 'solana', 'polkadot', 'ripple', 'dogecoin', 'avalanche', 'chainlink', 'polygon'],
    'symbol': ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'XRP', 'DOGE', 'AVAX', 'LINK', 'MATIC'],
    'name': ['Bitcoin', 'Ethereum', 'Cardano', 'Solana', 'Polkadot', 'XRP', 'Dogecoin', 'Avalanche', 'Chainlink', 'Polygon'],
    'current_price': [45000.0, 3000.0, 0.50, 100.0, 7.5, 0.60, 0.10, 35.0, 15.0, 0.90],
    'market_cap': [900000000000, 350000000000, 15000000000, 40000000000, 9000000000, 30000000000, 14000000000, 12000000000, 7000000000, 8000000000],
    'total_volume': [30000000000, 15000000000, 1000000000, 2000000000, 500000000, 2500000000, 1200000000, 800000000, 600000000, 700000000],
    'price_change_24h': [500.0, 50.0, 0.02, 5.0, 0.3, 0.05, 0.01, 2.0, 1.0, 0.05],
    'price_change_percentage_24h': [1.1, 1.7, 4.2, 5.3, 4.1, 9.1, 11.2, 6.1, 7.1, 5.9],
    'last_updated': ['2024-12-25T10:00:00Z'] * 10
}

# Create DataFrame
df = pd.DataFrame(data)

# Ensure data directory exists
output_path = Path('data/crypto_data.csv')
output_path.parent.mkdir(exist_ok=True)

# Save to CSV
df.to_csv(output_path, index=False)

print(f"✅ Sample CSV created successfully!")
print(f"📁 Location: {output_path.absolute()}")
print(f"📊 Total rows: {len(df)}")
print(f"\nFirst few rows:")
print(df.head())
