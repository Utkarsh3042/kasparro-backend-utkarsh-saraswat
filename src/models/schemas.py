from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CryptoData(BaseModel):
    """Unified cryptocurrency data model with canonical ID"""
    id: str  # Source-specific ID
    canonical_id: Optional[str] = None  # Normalized canonical ID for deduplication
    symbol: str
    name: str
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    total_volume: Optional[float] = None
    price_change_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None
    last_updated: datetime
    source: str  # 'csv', 'coingecko', or 'coinpaprika'
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "bitcoin",
                "canonical_id": "btc",
                "symbol": "BTC",
                "name": "Bitcoin",
                "current_price": 45000.0,
                "market_cap": 900000000000.0,
                "source": "coingecko"
            }
        }

class CryptoResponse(BaseModel):
    """API response model"""
    total: int
    page: int
    page_size: int
    data: List[CryptoData]

class StatsResponse(BaseModel):
    """Statistics response model"""
    total_coins: int
    total_market_cap: float
    total_volume: float
    avg_price: float
    top_gainers: List[CryptoData]
    top_losers: List[CryptoData]