from sqlalchemy import Column, String, Numeric, DateTime, Integer, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Cryptocurrency(Base):
    """ORM model for cryptocurrencies table"""
    __tablename__ = "cryptocurrencies"
    
    # Primary key
    canonical_id = Column(String(255), primary_key=True, index=True)
    
    # Required fields
    symbol = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # Numeric fields
    current_price = Column(Numeric(20, 8), nullable=True)
    market_cap = Column(Numeric(30, 2), nullable=True, index=True)
    total_volume = Column(Numeric(30, 2), nullable=True)
    price_change_24h = Column(Numeric(20, 8), nullable=True)
    price_change_percentage_24h = Column(Numeric(10, 4), nullable=True)
    
    # Timestamps
    last_updated = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_crypto_symbol', 'symbol'),
        Index('idx_crypto_market_cap', 'market_cap'),
    )
    
    def __repr__(self):
        return f"<Cryptocurrency(canonical_id='{self.canonical_id}', symbol='{self.symbol}', name='{self.name}')>"
    
    def to_dict(self):
        """Convert ORM object to dictionary"""
        return {
            'canonical_id': self.canonical_id,
            'symbol': self.symbol,
            'name': self.name,
            'current_price': float(self.current_price) if self.current_price else None,
            'market_cap': float(self.market_cap) if self.market_cap else None,
            'total_volume': float(self.total_volume) if self.total_volume else None,
            'price_change_24h': float(self.price_change_24h) if self.price_change_24h else None,
            'price_change_percentage_24h': float(self.price_change_percentage_24h) if self.price_change_percentage_24h else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SourceMapping(Base):
    """ORM model for source_mappings table"""
    __tablename__ = "source_mappings"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to cryptocurrencies
    canonical_id = Column(String(255), ForeignKey('cryptocurrencies.canonical_id'), nullable=False, index=True)
    
    # Source information
    source = Column(String(50), nullable=False)
    source_id = Column(String(255), nullable=False)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_source_canonical', 'canonical_id'),
        Index('idx_source_lookup', 'source', 'source_id'),
        Index('idx_source_unique', 'source', 'source_id', unique=True),
    )
    
    def __repr__(self):
        return f"<SourceMapping(canonical_id='{self.canonical_id}', source='{self.source}', source_id='{self.source_id}')>"
    
    def to_dict(self):
        """Convert ORM object to dictionary"""
        return {
            'id': self.id,
            'canonical_id': self.canonical_id,
            'source': self.source,
            'source_id': self.source_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }