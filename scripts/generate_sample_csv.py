import pandas as pd
import random
from pathlib import Path
from datetime import datetime
import argparse

def generate_static_data():
    """Generate fixed sample data (your original approach)"""
    data = {
        'id': ['bitcoin', 'ethereum', 'cardano', 'solana', 'polkadot', 'ripple', 'dogecoin', 'avalanche', 'chainlink', 'polygon'],
        'symbol': ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'XRP', 'DOGE', 'AVAX', 'LINK', 'MATIC'],
        'name': ['Bitcoin', 'Ethereum', 'Cardano', 'Solana', 'Polkadot', 'XRP', 'Dogecoin', 'Avalanche', 'Chainlink', 'Polygon'],
        'current_price': [45000.0, 3000.0, 0.50, 100.0, 7.5, 0.60, 0.10, 35.0, 15.0, 0.90],
        'market_cap': [900000000000, 350000000000, 15000000000, 40000000000, 9000000000, 30000000000, 14000000000, 12000000000, 7000000000, 8000000000],
        'total_volume': [30000000000, 15000000000, 1000000000, 2000000000, 500000000, 2500000000, 1200000000, 800000000, 600000000, 700000000],
        'price_change_24h': [500.0, 50.0, 0.02, 5.0, 0.3, 0.05, 0.01, 2.0, 1.0, 0.05],
        'price_change_percentage_24h': [1.1, 1.7, 4.2, 5.3, 4.1, 9.1, 11.2, 6.1, 7.1, 5.9],
        'last_updated': [datetime.now().isoformat()] * 10
    }
    return pd.DataFrame(data)

def generate_random_data(num_records=100):
    """Generate randomized sample data"""
    base_cryptos = [
        ('bitcoin', 'BTC', 'Bitcoin'),
        ('ethereum', 'ETH', 'Ethereum'),
        ('cardano', 'ADA', 'Cardano'),
        ('solana', 'SOL', 'Solana'),
        ('polkadot', 'DOT', 'Polkadot'),
    ]
    
    data = []
    for i in range(num_records):
        if i < len(base_cryptos):
            crypto_id, symbol, name = base_cryptos[i]
        else:
            crypto_id = f"coin{i}"
            symbol = f"COIN{i}"
            name = f"Test Coin {i}"
        
        price = random.uniform(0.01, 50000)
        market_cap = price * random.uniform(1e6, 1e11)
        
        data.append({
            'id': crypto_id,
            'symbol': symbol,
            'name': name,
            'current_price': round(price, 8),
            'market_cap': round(market_cap, 2),
            'total_volume': round(market_cap * random.uniform(0.01, 0.5), 2),
            'price_change_24h': round(random.uniform(-10, 10), 8),
            'price_change_percentage_24h': round(random.uniform(-20, 20), 4),
            'last_updated': datetime.now().isoformat()
        })
    
    return pd.DataFrame(data)

def generate_edge_cases():
    """Generate problematic data for testing error handling"""
    data = [
        # Missing symbol
        {'id': 'missing-symbol', 'symbol': '', 'name': 'No Symbol', 'current_price': 100},
        
        # Negative price
        {'id': 'negative', 'symbol': 'NEG', 'name': 'Negative', 'current_price': -100, 'market_cap': -1000},
        
        # Invalid price (will be string in CSV)
        {'id': 'invalid', 'symbol': 'INV', 'name': 'Invalid', 'current_price': 'not_a_number'},
        
        # Extremely large values
        {'id': 'extreme', 'symbol': 'EXT', 'name': 'Extreme', 'current_price': 1e100},
    ]
    return pd.DataFrame(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate sample cryptocurrency CSV data')
    parser.add_argument('--mode', choices=['static', 'random', 'edge'], default='static',
                        help='Data generation mode (default: static)')
    parser.add_argument('--records', type=int, default=100,
                        help='Number of records for random mode (default: 100)')
    parser.add_argument('--output', type=str, default='data/crypto_data.csv',
                        help='Output CSV file path (default: data/crypto_data.csv)')
    
    args = parser.parse_args()
    
    # Generate data based on mode
    if args.mode == 'static':
        df = generate_static_data()
        print(f"📊 Generating {len(df)} static records...")
    elif args.mode == 'random':
        df = generate_random_data(args.records)
        print(f"📊 Generating {len(df)} random records...")
    else:  # edge
        df = generate_edge_cases()
        print(f"📊 Generating {len(df)} edge case records...")
    
    # Ensure data directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    print(f"✅ Sample CSV created successfully!")
    print(f"📁 Location: {output_path.absolute()}")
    print(f"📊 Total rows: {len(df)}")
    print(f"\nFirst few rows:")
    print(df.head())
