import requests
from typing import List, Optional
from datetime import datetime
from src.models.schemas import CryptoData
from src.config import get_settings
from src.ingestion.base import BaseDataSource
from src.utils.retry import retry_with_backoff, retry_on_status_codes, CircuitBreaker
from src.utils.rate_limiter import AdaptiveRateLimiter

class CoinPaprikaSource(BaseDataSource):
    # Rate limiter: 25 calls per minute (free tier, conservative)
    rate_limiter = AdaptiveRateLimiter(max_calls=25, time_window=60, name="CoinPaprika")
    
    # Circuit breaker
    circuit_breaker = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=requests.RequestException,
        name="CoinPaprika"
    )
    
    def __init__(self):
        super().__init__("CoinPaprika")
        self.settings = get_settings()
        self.base_url = self.settings.coinpaprika_api_url
        self.api_key = self.settings.coinpaprika_api_key
        self.headers = {'Authorization': self.api_key} if self.api_key else {}
        self.timeout = 10
    
    @circuit_breaker
    @retry_on_status_codes(status_codes=[429, 500, 502, 503, 504], max_retries=3, base_delay=2.0)
    @retry_with_backoff(max_retries=3, base_delay=2.0, exponential_base=2.0, jitter=True)
    def fetch_coins(self, limit: int = 100) -> List[CryptoData]:
        """
        Fetch cryptocurrency data from CoinPaprika with rate limiting
        
        Rate limit: 25 calls/minute (conservative for free tier)
        Retry: Up to 3 attempts with exponential backoff
        Circuit breaker: Opens after 5 consecutive failures
        """
        coins_url = f"{self.base_url}/coins"
        
        try:
            self.logger.info(f"Fetching coins list from CoinPaprika...")
            
            # Apply rate limiting
            self.rate_limiter.wait_if_needed()
            
            response = requests.get(coins_url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 429:
                self.rate_limiter.on_rate_limit_error()
                response.raise_for_status()
            
            response.raise_for_status()
            self.rate_limiter.on_success()
            
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
        
        except requests.HTTPError as e:
            if e.response and e.response.status_code == 429:
                self.logger.error("CoinPaprika rate limit exceeded. Reduce request frequency.")
            self.log_error(e)
            raise
        
        except Exception as e:
            self.log_error(e)
            raise
    
    @circuit_breaker
    @retry_on_status_codes(status_codes=[429, 500, 502, 503, 504], max_retries=2, base_delay=1.0)
    def _fetch_ticker(self, coin_id: str) -> Optional[dict]:
        """Fetch ticker data for a specific coin with rate limiting"""
        url = f"{self.base_url}/tickers/{coin_id}"
        
        try:
            # Apply rate limiting
            self.rate_limiter.wait_if_needed()
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 429:
                self.rate_limiter.on_rate_limit_error()
                response.raise_for_status()
            
            response.raise_for_status()
            self.rate_limiter.on_success()
            
            return response.json()
        except Exception:
            return None
    
    def _parse_ticker_data(self, ticker: dict, coin: dict) -> CryptoData:
        """Parse ticker data from CoinPaprika API response"""
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
    
    def get_rate_limit_stats(self) -> dict:
        """Get current rate limiter statistics"""
        return self.rate_limiter.get_stats()
    
    def get_circuit_breaker_state(self) -> dict:
        """Get current circuit breaker state"""
        return self.circuit_breaker.get_state()