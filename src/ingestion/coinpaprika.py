import requests
from typing import List, Optional
from datetime import datetime
from src.models.schemas import CryptoData
from src.config import get_settings
from src.ingestion.base import BaseDataSource
from src.utils.retry import retry_with_backoff

class CoinPaprikaSource(BaseDataSource):
    def __init__(self):
        super().__init__("CoinPaprika")
        self.settings = get_settings()
        self.base_url = self.settings.coinpaprika_api_url
        self.api_key = self.settings.coinpaprika_api_key
        self.headers = {'Authorization': self.api_key} if self.api_key else {}
        self.timeout = 10
    
    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def fetch_coins(self, limit: int = 100) -> List[CryptoData]:
        """Fetch cryptocurrency data from CoinPaprika"""
        coins_url = f"{self.base_url}/coins"
        
        try:
            self.logger.info(f"Fetching coins list from CoinPaprika...")
            response = requests.get(coins_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            all_coins = response.json()
            
            if not self.validate_response(all_coins):
                return []
            
            active_coins = [c for c in all_coins if c.get('is_active', False)][:limit]
            
            crypto_list = []
            self.logger.info(f"Fetching ticker data for {min(len(active_coins), 50)} coins...")
            
            for i, coin in enumerate(active_coins[:50], 1):
                try:
                    ticker = self._fetch_ticker(coin['id'])
                    if ticker:
                        crypto_list.append(self._parse_ticker_data(ticker, coin))
                    
                    if i % 10 == 0:
                        self.logger.info(f"Progress: {i}/{min(len(active_coins), 50)} coins processed")
                
                except Exception as e:
                    self.logger.warning(f"Failed to fetch ticker for {coin.get('id')}: {e}")
                    continue
            
            self.log_success(len(crypto_list))
            return crypto_list
        
        except Exception as e:
            self.log_error(e)
            raise
    
    @retry_with_backoff(max_retries=2, base_delay=1.0)
    def _fetch_ticker(self, coin_id: str) -> Optional[dict]:
        """Fetch ticker data for a specific coin"""
        url = f"{self.base_url}/tickers/{coin_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
    
    def _parse_ticker_data(self, ticker: dict, coin: dict) -> CryptoData:
        """Parse ticker data"""
        quotes = ticker.get('quotes', {}).get('USD', {})
        
        return CryptoData(
            id=ticker.get('id', coin['id']),
            symbol=ticker.get('symbol', coin['symbol']).upper(),
            name=ticker.get('name', coin['name']),
            current_price=quotes.get('price'),
            market_cap=quotes.get('market_cap'),
            total_volume=quotes.get('volume_24h'),
            price_change_24h=None,
            price_change_percentage_24h=quotes.get('percent_change_24h'),
            last_updated=datetime.now(),
            source='coinpaprika'
        )
    
    def fetch_coin_by_id(self, coin_id: str) -> Optional[CryptoData]:
        """Fetch single coin data"""
        return None