from abc import ABC, abstractmethod
from typing import List, Optional
from src.models.schemas import CryptoData
from src.utils.logger import get_logger

class BaseDataSource(ABC):
    """Abstract base class for all data sources"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = get_logger(f"{__name__}.{source_name}")
    
    @abstractmethod
    def fetch_coins(self, limit: int) -> List[CryptoData]:
        """Fetch cryptocurrency data"""
        pass
    
    @abstractmethod
    def fetch_coin_by_id(self, coin_id: str) -> Optional[CryptoData]:
        """Fetch single coin data"""
        pass
    
    def validate_response(self, data: any) -> bool:
        """Validate API response"""
        if not data:
            self.logger.warning(f"{self.source_name}: Empty response received")
            return False
        return True
    
    def log_success(self, count: int):
        """Log successful data fetch"""
        self.logger.info(f"{self.source_name}: Successfully fetched {count} records")
    
    def log_error(self, error: Exception):
        """Log error during data fetch"""
        self.logger.error(f"{self.source_name}: Error fetching data - {str(error)}")