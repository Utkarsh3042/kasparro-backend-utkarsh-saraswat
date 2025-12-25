from typing import List, Optional
from src.models.schemas import CryptoData
from datetime import datetime

class DataStorage:
    """In-memory data storage with normalization support"""
    
    def __init__(self):
        self.data: List[CryptoData] = []
        self.last_updated: Optional[datetime] = None
    
    def add_records(self, records: List[CryptoData], normalize: bool = True):
        """Add new records to storage with optional normalization and deduplication"""
        if normalize:
            from src.utils.normalizer import DataNormalizer
            
            # Normalize incoming records
            normalized_records = [DataNormalizer.normalize(r) for r in records]
            
            # Combine with existing data
            all_records = self.data + normalized_records
            
            # Deduplicate based on canonical ID
            self.data = DataNormalizer.deduplicate(all_records)
        else:
            self.data.extend(records)
        
        self.last_updated = datetime.now()
    
    def clear(self):
        """Clear all data"""
        self.data = []
        self.last_updated = None
    
    def get_all(self) -> List[CryptoData]:
        """Get all records"""
        return self.data
    
    def get_by_canonical_id(self, canonical_id: str) -> Optional[CryptoData]:
        """Get record by canonical ID"""
        for record in self.data:
            if record.canonical_id == canonical_id:
                return record
        return None
    
    def get_by_symbol(self, symbol: str) -> List[CryptoData]:
        """Get records by symbol"""
        return [d for d in self.data if d.symbol.upper() == symbol.upper()]
    
    def get_count(self) -> int:
        """Get total count"""
        return len(self.data)

# Global storage instance
storage = DataStorage()