from pydantic import BaseModel, Field, validator
from typing import Optional, List, Generic, TypeVar
from datetime import datetime

# Generic type for pagination
T = TypeVar('T')

class CryptoData(BaseModel):
    """Schema for cryptocurrency data"""
    id: str = Field(..., description="Canonical identifier")
    symbol: str = Field(..., description="Trading symbol (e.g., BTC)")
    name: str = Field(..., description="Full name (e.g., Bitcoin)")
    current_price: Optional[float] = Field(None, description="Current price in USD")
    market_cap: Optional[float] = Field(None, description="Total market capitalization")
    total_volume: Optional[float] = Field(None, description="24h trading volume")
    price_change_24h: Optional[float] = Field(None, description="24h price change in USD")
    price_change_percentage_24h: Optional[float] = Field(None, description="24h price change percentage")
    last_updated: datetime = Field(..., description="Last update timestamp")
    source: str = Field(default="unknown", description="Data source (csv, coingecko, coinpaprika)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "current_price": 45000.0,
                "market_cap": 900000000000.0,
                "total_volume": 30000000000.0,
                "price_change_24h": 500.0,
                "price_change_percentage_24h": 1.1,
                "last_updated": "2024-12-25T10:00:00Z",
                "source": "coingecko"
            }
        }

    @validator('symbol')
    def symbol_must_be_uppercase(cls, v):
        """Ensure symbol is uppercase"""
        return v.upper() if v else v

    @validator('id', 'name')
    def string_must_not_be_empty(cls, v):
        """Ensure required strings are not empty"""
        if not v or not v.strip():
            raise ValueError('Must not be empty')
        return v.strip()


class IngestionResponse(BaseModel):
    """Response model for data ingestion endpoints"""
    success: bool = Field(..., description="Whether ingestion was successful")
    message: str = Field(..., description="Status message")
    records_ingested: int = Field(..., description="Number of records successfully ingested")
    source: str = Field(..., description="Data source used")
    timestamp: datetime = Field(..., description="Ingestion timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully ingested 100 records from CSV",
                "records_ingested": 100,
                "source": "csv",
                "timestamp": "2024-12-28T10:00:00Z"
            }
        }


class StatsResponse(BaseModel):
    """Response model for statistics endpoint"""
    total_cryptocurrencies: int = Field(..., description="Total number of cryptocurrencies")
    average_price: float = Field(..., description="Average price across all cryptocurrencies")
    total_market_cap: float = Field(..., description="Total market capitalization")
    top_by_market_cap: list = Field(..., description="Top 5 cryptocurrencies by market cap")
    sources: dict = Field(..., description="Number of records per source")

    class Config:
        json_schema_extra = {
            "example": {
                "total_cryptocurrencies": 150,
                "average_price": 1250.50,
                "total_market_cap": 2500000000000.0,
                "top_by_market_cap": [
                    {
                        "symbol": "BTC",
                        "name": "Bitcoin",
                        "market_cap": 900000000000.0
                    }
                ],
                "sources": {
                    "csv": 50,
                    "coingecko": 50,
                    "coinpaprika": 50
                }
            }
        }


class ErrorResponse(BaseModel):
    """Response model for error responses"""
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: datetime = Field(..., description="Error timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "ValidationError",
                "message": "Invalid data format",
                "timestamp": "2024-12-28T10:00:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(..., description="System status")
    message: str = Field(..., description="Status message")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Check timestamp")
    database: dict = Field(..., description="Database status")
    features: dict = Field(..., description="Enabled features")
    sources: list = Field(..., description="Available data sources")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "message": "Crypto ETL Backend is running",
                "version": "2.0.0",
                "timestamp": "2024-12-28T10:00:00Z",
                "database": {
                    "connected": True,
                    "total_records": 150,
                    "last_updated": "2024-12-28T09:30:00Z"
                },
                "features": {
                    "csv_ingestion": True,
                    "api_ingestion": True,
                    "normalization": True,
                    "orm": True
                },
                "sources": ["csv", "coingecko", "coinpaprika"]
            }
        }


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number (starts from 1)")
    page_size: int = Field(100, ge=1, le=1000, description="Items per page (max: 1000)")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.page_size
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 100
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    data: List[T] = Field(..., description="List of items for current page")
    pagination: dict = Field(..., description="Pagination metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin"}
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 100,
                    "total_items": 150,
                    "total_pages": 2,
                    "has_next": True,
                    "has_previous": False
                }
            }
        }


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_previous: bool = Field(..., description="Whether there's a previous page")
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 100,
                "total_items": 150,
                "total_pages": 2,
                "has_next": True,
                "has_previous": False
            }
        }