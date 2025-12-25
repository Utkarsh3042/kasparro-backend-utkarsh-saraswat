import requests
from typing import List, Optional
from datetime import datetime
from src.models.schemas import CryptoData
from src.config import get_settings
from src.ingestion.base import BaseDataSource
from src.utils.retry import retry_with_backoff

class CoinGeckoSource(BaseDataSource):
    def __init__(self):
        super().__init__("CoinGecko")
        self.settings = get_settings()
        self.base_url = self.settings.coingecko_api_url
        self.timeout = 10
    
    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def fetch_coins(self, limit: int = 100) -> List[CryptoData]:
        """Fetch cryptocurrency data from CoinGecko"""
        url = f"{self.base_url}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': min(limit, 250),
            'page': 1,
            'sparkline': False
        }
        
        try:
            self.logger.info(f"Fetching {limit} coins from CoinGecko...")
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if not self.validate_response(data):
                return []
            
            crypto_list = []
            for coin in data:
                try:
                    crypto_list.append(self._parse_coin_data(coin))
                except Exception as e:
                    self.logger.warning(f"Failed to parse coin {coin.get('id', 'unknown')}: {e}")
                    continue
            
            self.log_success(len(crypto_list))
            return crypto_list
        
        except Exception as e:
            self.log_error(e)
            raise
    
    def _parse_coin_data(self, coin: dict) -> CryptoData:
        """Parse coin data"""
        return CryptoData(
            id=coin['id'],
            symbol=coin['symbol'].upper(),
            name=coin['name'],
            current_price=coin.get('current_price'),
            market_cap=coin.get('market_cap'),
            total_volume=coin.get('total_volume'),
            price_change_24h=coin.get('price_change_24h'),
            price_change_percentage_24h=coin.get('price_change_percentage_24h'),
            last_updated=datetime.fromisoformat(coin['last_updated'].replace('Z', '+00:00')),
            source='coingecko'
        )
    
    def fetch_coin_by_id(self, coin_id: str) -> Optional[CryptoData]:
        """Fetch single coin data"""
        # Implementation similar to fetch_coins but for single coin
        return None