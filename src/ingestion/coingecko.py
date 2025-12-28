import requests
from typing import List, Optional
from datetime import datetime
from src.models.schemas import CryptoData
from src.config import get_settings
from src.ingestion.base import BaseDataSource
from src.utils.retry import retry_with_backoff, retry_on_status_codes, CircuitBreaker
from src.utils.rate_limiter import AdaptiveRateLimiter

class CoinGeckoSource(BaseDataSource):
    # Rate limiter: 50 calls per minute (free tier)
    rate_limiter = AdaptiveRateLimiter(max_calls=50, time_window=60, name="CoinGecko")
    
    # Circuit breaker: Open after 5 failures, recovery timeout 60s
    circuit_breaker = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=60,
        expected_exception=requests.RequestException,
        name="CoinGecko"
    )
    
    def __init__(self):
        super().__init__("CoinGecko")
        self.settings = get_settings()
        self.base_url = self.settings.coingecko_api_url
        self.timeout = 10
    
    @circuit_breaker
    @retry_on_status_codes(status_codes=[429, 500, 502, 503, 504], max_retries=3, base_delay=2.0)
    @retry_with_backoff(max_retries=3, base_delay=2.0, exponential_base=2.0, jitter=True)
    def fetch_coins(self, limit: int = 100) -> List[CryptoData]:
        """
        Fetch cryptocurrency data from CoinGecko with rate limiting and retry logic
        
        Rate limit: 50 calls/minute (free tier)
        Retry: Up to 3 attempts with exponential backoff
        Circuit breaker: Opens after 5 consecutive failures
        """
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
            
            # Apply rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Make API call
            response = requests.get(url, params=params, timeout=self.timeout)
            
            # Handle rate limit response
            if response.status_code == 429:
                self.rate_limiter.on_rate_limit_error()
                response.raise_for_status()
            
            response.raise_for_status()
            
            # Success - notify adaptive rate limiter
            self.rate_limiter.on_success()
            
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
        
        except requests.HTTPError as e:
            if e.response and e.response.status_code == 429:
                self.logger.error("CoinGecko rate limit exceeded. Consider upgrading API tier.")
            self.log_error(e)
            raise
        
        except Exception as e:
            self.log_error(e)
            raise
    
    def _parse_coin_data(self, coin: dict) -> CryptoData:
        """Parse coin data from CoinGecko API response"""
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
    
    @circuit_breaker
    @retry_on_status_codes(status_codes=[429, 500, 502, 503, 504], max_retries=3)
    def fetch_coin_by_id(self, coin_id: str) -> Optional[CryptoData]:
        """Fetch single coin data with rate limiting"""
        url = f"{self.base_url}/coins/{coin_id}"
        
        try:
            self.rate_limiter.wait_if_needed()
            
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 429:
                self.rate_limiter.on_rate_limit_error()
                response.raise_for_status()
            
            response.raise_for_status()
            self.rate_limiter.on_success()
            
            coin = response.json()
            return self._parse_coin_data(coin.get('market_data', {}))
        
        except Exception as e:
            self.logger.error(f"Failed to fetch coin {coin_id}: {e}")
            return None
    
    def get_rate_limit_stats(self) -> dict:
        """Get current rate limiter statistics"""
        return self.rate_limiter.get_stats()
    
    def get_circuit_breaker_state(self) -> dict:
        """Get current circuit breaker state"""
        return self.circuit_breaker.get_state()