from typing import List, Optional, Dict, Tuple
from datetime import datetime
from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError
from src.models.schemas import CryptoData
from src.database.connection import get_db
from src.database.models import Cryptocurrency, SourceMapping
from src.utils.logger import get_logger

logger = get_logger(__name__)

class CryptoStorage:
    """Database storage layer using SQLAlchemy ORM"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._last_updated = None
    
    @property
    def last_updated(self) -> Optional[datetime]:
        """Get the most recent update timestamp from database"""
        try:
            with get_db() as db:
                result = db.query(func.max(Cryptocurrency.updated_at)).scalar()
                return result
        except Exception as e:
            self.logger.error(f"Error fetching last_updated: {e}")
            return None
    
    def store(self, data: List[CryptoData]) -> int:
        """
        Store cryptocurrency data using ORM
        
        Args:
            data: List of CryptoData objects
            
        Returns:
            Number of records stored
        """
        if not data:
            return 0
        
        stored_count = 0
        
        try:
            with get_db() as db:
                for crypto in data:
                    try:
                        # Check if cryptocurrency exists
                        existing = db.query(Cryptocurrency).filter(
                            Cryptocurrency.canonical_id == crypto.id
                        ).first()
                        
                        if existing:
                            # Update existing record
                            existing.symbol = crypto.symbol
                            existing.name = crypto.name
                            existing.current_price = crypto.current_price
                            existing.market_cap = crypto.market_cap
                            existing.total_volume = crypto.total_volume
                            existing.price_change_24h = crypto.price_change_24h
                            existing.price_change_percentage_24h = crypto.price_change_percentage_24h
                            existing.last_updated = crypto.last_updated
                            existing.updated_at = datetime.now()
                            
                            self.logger.debug(f"Updated: {crypto.symbol} ({crypto.id})")
                        else:
                            # Insert new record
                            new_crypto = Cryptocurrency(
                                canonical_id=crypto.id,
                                symbol=crypto.symbol,
                                name=crypto.name,
                                current_price=crypto.current_price,
                                market_cap=crypto.market_cap,
                                total_volume=crypto.total_volume,
                                price_change_24h=crypto.price_change_24h,
                                price_change_percentage_24h=crypto.price_change_percentage_24h,
                                last_updated=crypto.last_updated
                            )
                            db.add(new_crypto)
                            self.logger.debug(f"Inserted: {crypto.symbol} ({crypto.id})")
                        
                        # Store source mapping
                        self._store_source_mapping(db, crypto.id, crypto.source, crypto.id)
                        
                        stored_count += 1
                        
                    except IntegrityError as e:
                        self.logger.warning(f"Integrity error for {crypto.symbol}: {e}")
                        db.rollback()
                        continue
                    except Exception as e:
                        self.logger.error(f"Error storing {crypto.symbol}: {e}")
                        db.rollback()
                        continue
                
                db.commit()
                self.logger.info(f"✅ Stored {stored_count} records in database")
                
        except Exception as e:
            self.logger.error(f"Storage operation failed: {e}")
            raise
        
        return stored_count
    
    def _store_source_mapping(self, db, canonical_id: str, source: str, source_id: str):
        """Store source mapping"""
        try:
            existing = db.query(SourceMapping).filter(
                SourceMapping.source == source,
                SourceMapping.source_id == source_id
            ).first()
            
            if not existing:
                mapping = SourceMapping(
                    canonical_id=canonical_id,
                    source=source,
                    source_id=source_id
                )
                db.add(mapping)
        except Exception as e:
            self.logger.debug(f"Source mapping already exists or error: {e}")
    
    def get_all(self, page: int = 1, page_size: int = 100) -> Tuple[List[Dict], int]:
        """
        Get all cryptocurrencies with pagination
        
        Args:
            page: Page number (starts from 1)
            page_size: Items per page
            
        Returns:
            Tuple of (list of crypto dicts, total count)
        """
        try:
            with get_db() as db:
                # Get total count
                total_count = db.query(Cryptocurrency).count()
                
                # Get paginated results
                offset = (page - 1) * page_size
                
                cryptos = db.query(Cryptocurrency)\
                    .order_by(desc(Cryptocurrency.market_cap))\
                    .offset(offset)\
                    .limit(page_size)\
                    .all()
                
                return [crypto.to_dict() for crypto in cryptos], total_count
        except Exception as e:
            self.logger.error(f"Error fetching all data: {e}")
            return [], 0
    
    def get_by_canonical_id(self, canonical_id: str) -> Optional[Dict]:
        """Get cryptocurrency by canonical ID"""
        try:
            with get_db() as db:
                crypto = db.query(Cryptocurrency).filter(
                    Cryptocurrency.canonical_id == canonical_id
                ).first()
                
                return crypto.to_dict() if crypto else None
        except Exception as e:
            self.logger.error(f"Error fetching by ID {canonical_id}: {e}")
            return None
    
    def get_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get cryptocurrency by symbol"""
        try:
            with get_db() as db:
                crypto = db.query(Cryptocurrency).filter(
                    Cryptocurrency.symbol == symbol.upper()
                ).first()
                
                return crypto.to_dict() if crypto else None
        except Exception as e:
            self.logger.error(f"Error fetching by symbol {symbol}: {e}")
            return None
    
    def get_count(self) -> int:
        """Get total count of cryptocurrencies"""
        try:
            with get_db() as db:
                return db.query(Cryptocurrency).count()
        except Exception as e:
            self.logger.error(f"Error counting records: {e}")
            return 0
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            with get_db() as db:
                total = db.query(Cryptocurrency).count()
                
                avg_price = db.query(func.avg(Cryptocurrency.current_price)).scalar()
                total_market_cap = db.query(func.sum(Cryptocurrency.market_cap)).scalar()
                
                top_by_market_cap = db.query(Cryptocurrency)\
                    .order_by(desc(Cryptocurrency.market_cap))\
                    .limit(5)\
                    .all()
                
                sources_count = db.query(
                    SourceMapping.source,
                    func.count(SourceMapping.id)
                ).group_by(SourceMapping.source).all()
                
                return {
                    'total_cryptocurrencies': total,
                    'average_price': float(avg_price) if avg_price else 0.0,
                    'total_market_cap': float(total_market_cap) if total_market_cap else 0.0,
                    'top_by_market_cap': [crypto.to_dict() for crypto in top_by_market_cap],
                    'sources': {source: count for source, count in sources_count}
                }
        except Exception as e:
            self.logger.error(f"Error fetching statistics: {e}")
            return {}
    
    def clear(self):
        """Clear all data from database"""
        try:
            with get_db() as db:
                db.query(SourceMapping).delete()
                db.query(Cryptocurrency).delete()
                db.commit()
                self.logger.info("🗑️  Database cleared")
        except Exception as e:
            self.logger.error(f"Error clearing database: {e}")
            raise
    
    def filter(
        self,
        symbol: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        source: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[List[Dict], int]:
        """
        Filter cryptocurrencies with pagination
        
        Returns:
            Tuple of (filtered results, total count)
        """
        try:
            with get_db() as db:
                query = db.query(Cryptocurrency)
                
                # Apply filters
                if symbol:
                    query = query.filter(Cryptocurrency.symbol.ilike(f"%{symbol}%"))
                
                if min_price is not None:
                    query = query.filter(Cryptocurrency.current_price >= min_price)
                
                if max_price is not None:
                    query = query.filter(Cryptocurrency.current_price <= max_price)
                
                if source:
                    query = query.join(SourceMapping).filter(SourceMapping.source == source)
                
                # Get total count
                total_count = query.count()
                
                # Apply pagination
                offset = (page - 1) * page_size
                results = query.order_by(desc(Cryptocurrency.market_cap))\
                    .offset(offset)\
                    .limit(page_size)\
                    .all()
                
                return [crypto.to_dict() for crypto in results], total_count
        except Exception as e:
            self.logger.error(f"Error filtering data: {e}")
            return [], 0

# Global storage instance
storage = CryptoStorage()