from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
from src.models.schemas import CryptoResponse, StatsResponse
from src.ingestion.coingecko import CoinGeckoSource
from src.ingestion.coinpaprika import CoinPaprikaSource
from src.ingestion.csv_source import CSVDataSource
from src.database.storage import storage
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/ingest/csv")
def ingest_csv(limit: int = Query(100, ge=1, le=1000)):
    """Ingest data from CSV file with normalization"""
    try:
        logger.info(f"Starting CSV ingestion (limit={limit})")
        source = CSVDataSource()
        records = source.fetch_coins(limit=limit)
        
        if records:
            storage.add_records(records, normalize=True)
            logger.info(f"Successfully ingested {len(records)} records from CSV")
            return {
                "status": "success",
                "message": f"Ingested {len(records)} records from CSV",
                "count": len(records),
                "normalized": True,
                "total_unique_coins": storage.get_count()
            }
        else:
            raise HTTPException(status_code=404, detail="No data found in CSV file")
            
    except FileNotFoundError:
        logger.error("CSV file not found")
        raise HTTPException(status_code=404, detail="CSV file not found. Please ensure data/crypto_data.csv exists")
        
    except Exception as e:
        logger.error(f"CSV ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/coingecko")
def ingest_coingecko(limit: int = Query(100, ge=1, le=250)):
    """Ingest data from CoinGecko API with normalization"""
    try:
        logger.info(f"Starting CoinGecko ingestion (limit={limit})")
        source = CoinGeckoSource()
        records = source.fetch_coins(limit=limit)
        
        if records:
            storage.add_records(records, normalize=True)
            logger.info(f"Successfully ingested {len(records)} records from CoinGecko")
            return {
                "status": "success",
                "message": f"Ingested {len(records)} records from CoinGecko",
                "count": len(records),
                "normalized": True,
                "total_unique_coins": storage.get_count()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch data from CoinGecko")
            
    except Exception as e:
        logger.error(f"CoinGecko ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/coinpaprika")
def ingest_coinpaprika(limit: int = Query(50, ge=1, le=100)):
    """Ingest data from CoinPaprika API with normalization"""
    try:
        logger.info(f"Starting CoinPaprika ingestion (limit={limit})")
        source = CoinPaprikaSource()
        records = source.fetch_coins(limit=limit)
        
        if records:
            storage.add_records(records, normalize=True)
            logger.info(f"Successfully ingested {len(records)} records from CoinPaprika")
            return {
                "status": "success",
                "message": f"Ingested {len(records)} records from CoinPaprika",
                "count": len(records),
                "normalized": True,
                "total_unique_coins": storage.get_count()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch data from CoinPaprika")
            
    except Exception as e:
        logger.error(f"CoinPaprika ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/ingest/all")
def ingest_all():
    """Ingest data from all sources (CSV, CoinGecko, CoinPaprika) with normalization"""
    logger.info("Starting ingestion from all sources")
    
    results = {"csv": {}, "coingecko": {}, "coinpaprika": {}}
    storage.clear()
    
    all_records = []
    
    # CSV Source
    try:
        logger.info("Ingesting from CSV...")
        csv_source = CSVDataSource()
        csv_records = csv_source.fetch_coins(limit=100)
        all_records.extend(csv_records)
        results["csv"] = {"status": "success", "count": len(csv_records)}
        logger.info(f"CSV: {len(csv_records)} records fetched")
    except Exception as e:
        logger.error(f"CSV ingestion failed: {str(e)}")
        results["csv"] = {"status": "failed", "error": str(e)}
    
    # CoinGecko Source
    try:
        logger.info("Ingesting from CoinGecko...")
        cg_source = CoinGeckoSource()
        cg_records = cg_source.fetch_coins(limit=100)
        all_records.extend(cg_records)
        results["coingecko"] = {"status": "success", "count": len(cg_records)}
        logger.info(f"CoinGecko: {len(cg_records)} records fetched")
    except Exception as e:
        logger.error(f"CoinGecko ingestion failed: {str(e)}")
        results["coingecko"] = {"status": "failed", "error": str(e)}
    
    # CoinPaprika Source
    try:
        logger.info("Ingesting from CoinPaprika...")
        cp_source = CoinPaprikaSource()
        cp_records = cp_source.fetch_coins(limit=50)
        all_records.extend(cp_records)
        results["coinpaprika"] = {"status": "success", "count": len(cp_records)}
        logger.info(f"CoinPaprika: {len(cp_records)} records fetched")
    except Exception as e:
        logger.error(f"CoinPaprika ingestion failed: {str(e)}")
        results["coinpaprika"] = {"status": "failed", "error": str(e)}
    
    # Add all records with normalization and deduplication
    if all_records:
        storage.add_records(all_records, normalize=True)
        logger.info(f"Total records after normalization: {storage.get_count()}")
    
    return {
        "status": "completed",
        "sources": results,
        "total_fetched": len(all_records),
        "total_unique_coins": storage.get_count(),
        "normalized": True,
        "deduplicated": True
    }


@router.get("/data", response_model=CryptoResponse)
def get_data(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    source: Optional[str] = None,
    symbol: Optional[str] = None
):
    """
    Retrieve cryptocurrency data with pagination and filtering
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)
    - **source**: Filter by source (csv, coingecko, coinpaprika)
    - **symbol**: Filter by symbol (e.g., BTC, ETH)
    """
    all_data = storage.get_all()
    
    # Apply filters
    if source:
        all_data = [d for d in all_data if d.source == source.lower()]
    
    if symbol:
        all_data = [d for d in all_data if d.symbol.upper() == symbol.upper()]
    
    # Pagination
    start = (page - 1) * page_size
    end = start + page_size
    paginated_data = all_data[start:end]
    
    return CryptoResponse(
        total=len(all_data),
        page=page,
        page_size=page_size,
        data=paginated_data
    )


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """
    Get comprehensive statistics about cryptocurrency data
    
    Returns:
    - Total coins count
    - Total market capitalization
    - Total trading volume
    - Average price
    - Top 5 gainers (24h)
    - Top 5 losers (24h)
    """
    all_data = storage.get_all()
    
    if not all_data:
        raise HTTPException(status_code=404, detail="No data available. Please ingest data first.")
    
    # Calculate aggregates
    valid_market_cap = [d.market_cap for d in all_data if d.market_cap]
    valid_volume = [d.total_volume for d in all_data if d.total_volume]
    valid_price = [d.current_price for d in all_data if d.current_price]
    
    # Sort by 24h change
    coins_with_change = [d for d in all_data if d.price_change_percentage_24h is not None]
    sorted_by_change = sorted(coins_with_change, key=lambda x: x.price_change_percentage_24h or 0, reverse=True)
    
    return StatsResponse(
        total_coins=len(all_data),
        total_market_cap=sum(valid_market_cap) if valid_market_cap else 0.0,
        total_volume=sum(valid_volume) if valid_volume else 0.0,
        avg_price=sum(valid_price) / len(valid_price) if valid_price else 0.0,
        top_gainers=sorted_by_change[:5],
        top_losers=sorted_by_change[-5:][::-1] if len(sorted_by_change) >= 5 else []
    )


@router.get("/coins/{canonical_id}")
def get_coin_by_id(canonical_id: str):
    """Get specific coin by canonical ID"""
    coin = storage.get_by_canonical_id(canonical_id.lower())
    
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin with canonical_id '{canonical_id}' not found")
    
    return coin


@router.delete("/data")
def clear_data():
    """Clear all stored cryptocurrency data"""
    count = storage.get_count()
    storage.clear()
    logger.info(f"Cleared {count} records from storage")
    
    return {
        "status": "success",
        "message": f"Cleared {count} records",
        "total_records": 0
    }