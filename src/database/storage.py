from typing import List, Optional
from src.models.schemas import CryptoData
from datetime import datetime

class DataStorage:
    """In-memory data storage"""
    
    def __init__(self):
        self.data: List[CryptoData] = []
        self.last_updated: Optional[datetime] = None
    
    def add_records(self, records: List[CryptoData]):
        """Add new records to storage"""
        self.data.extend(records)
        self.last_updated = datetime.now()
    
    def clear(self):
        """Clear all data"""
        self.data = []
        self.last_updated = None
    
    def get_all(self) -> List[CryptoData]:
        """Get all records"""
        return self.data
    
    def get_count(self) -> int:
        """Get total count"""
        return len(self.data)

# Global storage instance
storage = DataStorage()