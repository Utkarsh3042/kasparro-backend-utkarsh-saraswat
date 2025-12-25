from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CryptoData(BaseModel):
    """Unified cryptocurrency data model"""
    id: str
    symbol: str
    name: str
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    total_volume: Optional[float] = None
    price_change_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None
    last_updated: datetime
    source: str

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