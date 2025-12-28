from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Optional
from datetime import datetime
from src.models.schemas import (
    CryptoData, IngestionResponse, StatsResponse,
    PaginationParams, PaginationMeta
)
from src.ingestion.csv_source import CSVDataSource
from src.ingestion.coingecko import CoinGeckoSource
from src.ingestion.coinpaprika import CoinPaprikaSource
from src.database.storage import storage
from src.utils.normalizer import normalize_and_deduplicate
from src.utils.pagination import create_pagination_meta, get_pagination_links
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/ingest/csv", response_model=IngestionResponse)
async def ingest_csv(limit: int = Query(100, description="Maximum number of records to ingest")):
    """
    Ingest cryptocurrency data from CSV file
    
    - **limit**: Maximum number of records to fetch (default: 100)
    """
    try:
        logger.info(f"Starting CSV ingestion (limit={limit})")
        
        # Fetch data from CSV
        csv_source = CSVDataSource()
        raw_data = csv_source.fetch_coins(limit=limit)
        
        if not raw_data:
            logger.warning("No data fetched from CSV")
            return IngestionResponse(
                success=False,
                message="No data available in CSV",
                records_ingested=0,
                source="csv",
                timestamp=datetime.now()
            )
        
        # Normalize and deduplicate
        normalized_data = normalize_and_deduplicate(raw_data)
        
        # Store in database using ORM
        stored_count = storage.store(normalized_data)  # ✅ Changed from add_records
        
        logger.info(f"Successfully ingested {stored_count} records from CSV")
        
        return IngestionResponse(
            success=True,
            message=f"Successfully ingested {stored_count} records from CSV",
            records_ingested=stored_count,
            source="csv",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"CSV ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"CSV ingestion failed: {str(e)}")

@router.post("/ingest/coingecko", response_model=IngestionResponse)
async def ingest_coingecko(limit: int = Query(100, description="Maximum number of records to ingest")):
    """
    Ingest cryptocurrency data from CoinGecko API
    
    - **limit**: Maximum number of records to fetch (default: 100)
    """
    try:
        logger.info(f"Starting CoinGecko ingestion (limit={limit})")
        
        # Fetch data from CoinGecko
        coingecko_source = CoinGeckoSource()
        raw_data = coingecko_source.fetch_coins(limit=limit)
        
        if not raw_data:
            logger.warning("No data fetched from CoinGecko")
            return IngestionResponse(
                success=False,
                message="No data available from CoinGecko",
                records_ingested=0,
                source="coingecko",
                timestamp=datetime.now()
            )
        
        # Normalize and deduplicate
        normalized_data = normalize_and_deduplicate(raw_data)
        
        # Store in database using ORM
        stored_count = storage.store(normalized_data)  # ✅ Changed from add_records
        
        logger.info(f"Successfully ingested {stored_count} records from CoinGecko")
        
        return IngestionResponse(
            success=True,
            message=f"Successfully ingested {stored_count} records from CoinGecko",
            records_ingested=stored_count,
            source="coingecko",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"CoinGecko ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"CoinGecko ingestion failed: {str(e)}")

@router.post("/ingest/coinpaprika", response_model=IngestionResponse)
async def ingest_coinpaprika(limit: int = Query(100, description="Maximum number of records to ingest")):
    """
    Ingest cryptocurrency data from CoinPaprika API
    
    - **limit**: Maximum number of records to fetch (default: 100)
    """
    try:
        logger.info(f"Starting CoinPaprika ingestion (limit={limit})")
        
        # Fetch data from CoinPaprika
        coinpaprika_source = CoinPaprikaSource()
        raw_data = coinpaprika_source.fetch_coins(limit=limit)
        
        if not raw_data:
            logger.warning("No data fetched from CoinPaprika")
            return IngestionResponse(
                success=False,
                message="No data available from CoinPaprika",
                records_ingested=0,
                source="coinpaprika",
                timestamp=datetime.now()
            )
        
        # Normalize and deduplicate
        normalized_data = normalize_and_deduplicate(raw_data)
        
        # Store in database using ORM
        stored_count = storage.store(normalized_data)  # ✅ Changed from add_records
        
        logger.info(f"Successfully ingested {stored_count} records from CoinPaprika")
        
        return IngestionResponse(
            success=True,
            message=f"Successfully ingested {stored_count} records from CoinPaprika",
            records_ingested=stored_count,
            source="coinpaprika",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"CoinPaprika ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"CoinPaprika ingestion failed: {str(e)}")

@router.post("/ingest/all", response_model=IngestionResponse)
async def ingest_all(limit: int = Query(100, description="Maximum number of records per source")):
    """
    Ingest cryptocurrency data from all sources (CSV, CoinGecko, CoinPaprika)
    
    - **limit**: Maximum number of records to fetch per source (default: 100)
    """
    try:
        logger.info(f"Starting multi-source ingestion (limit={limit} per source)")
        
        all_data = []
        sources_used = []
        
        # Fetch from CSV
        try:
            csv_source = CSVDataSource()
            csv_data = csv_source.fetch_coins(limit=limit)
            if csv_data:
                all_data.extend(csv_data)
                sources_used.append("csv")
                logger.info(f"Fetched {len(csv_data)} records from CSV")
        except Exception as e:
            logger.warning(f"CSV fetch failed: {e}")
        
        # Fetch from CoinGecko
        try:
            coingecko_source = CoinGeckoSource()
            coingecko_data = coingecko_source.fetch_coins(limit=limit)
            if coingecko_data:
                all_data.extend(coingecko_data)
                sources_used.append("coingecko")
                logger.info(f"Fetched {len(coingecko_data)} records from CoinGecko")
        except Exception as e:
            logger.warning(f"CoinGecko fetch failed: {e}")
        
        # Fetch from CoinPaprika
        try:
            coinpaprika_source = CoinPaprikaSource()
            coinpaprika_data = coinpaprika_source.fetch_coins(limit=limit)
            if coinpaprika_data:
                all_data.extend(coinpaprika_data)
                sources_used.append("coinpaprika")
                logger.info(f"Fetched {len(coinpaprika_data)} records from CoinPaprika")
        except Exception as e:
            logger.warning(f"CoinPaprika fetch failed: {e}")
        
        if not all_data:
            logger.warning("No data fetched from any source")
            return IngestionResponse(
                success=False,
                message="No data available from any source",
                records_ingested=0,
                source="all",
                timestamp=datetime.now()
            )
        
        # Normalize and deduplicate
        normalized_data = normalize_and_deduplicate(all_data)
        
        # Store in database using ORM
        stored_count = storage.store(normalized_data)  # ✅ Changed from add_records
        
        logger.info(f"Successfully ingested {stored_count} records from {len(sources_used)} sources")
        
        return IngestionResponse(
            success=True,
            message=f"Successfully ingested {stored_count} records from sources: {', '.join(sources_used)}",
            records_ingested=stored_count,
            source="all",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Multi-source ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Multi-source ingestion failed: {str(e)}")

@router.get("/data")
async def get_all_data(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page (max: 1000)")
):
    """
    Get all cryptocurrency data with pagination
    
    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max: 1000)
    
    Returns paginated results with metadata
    """
    try:
        # Get paginated data from storage
        data, total_count = storage.get_all(page=page, page_size=page_size)
        
        # Create pagination metadata
        pagination_meta = create_pagination_meta(page, page_size, total_count)
        
        # Create pagination links
        base_url = str(request.url).split('?')[0]
        links = get_pagination_links(base_url, page, page_size, pagination_meta.total_pages)
        
        return {
            "data": data,
            "pagination": pagination_meta.dict(),
            "links": links
        }
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@router.get("/search")
async def search_coins(
    request: Request,
    symbol: Optional[str] = Query(None, description="Search by symbol"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    source: Optional[str] = Query(None, description="Filter by source"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page")
):
    """
    Search and filter cryptocurrencies with pagination
    
    - **symbol**: Filter by symbol (case-insensitive, partial match)
    - **min_price**: Minimum current price
    - **max_price**: Maximum current price
    - **source**: Filter by data source (csv, coingecko, coinpaprika)
    - **page**: Page number (starts from 1)
    - **page_size**: Items per page (max: 1000)
    """
    try:
        # Get filtered and paginated results
        results, total_count = storage.filter(
            symbol=symbol,
            min_price=min_price,
            max_price=max_price,
            source=source,
            page=page,
            page_size=page_size
        )
        
        # Create pagination metadata
        pagination_meta = create_pagination_meta(page, page_size, total_count)
        
        # Create pagination links
        base_url = str(request.url).split('?')[0]
        links = get_pagination_links(base_url, page, page_size, pagination_meta.total_pages)
        
        return {
            "data": results,
            "pagination": pagination_meta.dict(),
            "links": links,
            "filters": {
                "symbol": symbol,
                "min_price": min_price,
                "max_price": max_price,
                "source": source
            }
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/coins/{coin_id}")
async def get_coin_by_id(coin_id: str):
    """
    Get cryptocurrency by canonical ID
    
    - **coin_id**: Canonical identifier (e.g., 'btc', 'bitcoin')
    
    No pagination needed - returns single item
    """
    try:
        coin = storage.get_by_canonical_id(coin_id.lower())
        if not coin:
            raise HTTPException(status_code=404, detail=f"Coin '{coin_id}' not found")
        return coin
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching coin {coin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching coin: {str(e)}")


@router.get("/stats")
async def get_statistics():
    """
    Get database statistics and analytics
    
    No pagination needed - returns summary data
    
    Returns:
    - Total number of cryptocurrencies
    - Average price
    - Total market cap
    - Top 5 by market cap
    - Source distribution
    """
    try:
        stats = storage.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")


@router.delete("/data/clear")
async def clear_all_data():
    """
    Clear all data from database (use with caution!)
    
    No pagination needed - returns status only
    """
    try:
        storage.clear()
        logger.info("Database cleared successfully")
        return {
            "success": True,
            "message": "All data cleared from database",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing database: {str(e)}")

# Add this endpoint to monitor rate limiters and circuit breakers

@router.get("/status/api-health")
async def get_api_health():
    """
    Get health status of external APIs
    
    Returns:
    - Rate limiter statistics
    - Circuit breaker states
    - API availability
    """
    from src.ingestion.coingecko import CoinGeckoSource
    from src.ingestion.coinpaprika import CoinPaprikaSource
    
    try:
        coingecko = CoinGeckoSource()
        coinpaprika = CoinPaprikaSource()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "apis": {
                "coingecko": {
                    "rate_limiter": coingecko.get_rate_limit_stats(),
                    "circuit_breaker": coingecko.get_circuit_breaker_state()
                },
                "coinpaprika": {
                    "rate_limiter": coinpaprika.get_rate_limit_stats(),
                    "circuit_breaker": coinpaprika.get_circuit_breaker_state()
                }
            }
        }
    except Exception as e:
        logger.error(f"Error fetching API health: {e}")
        raise HTTPException(status_code=500, detail=str(e))