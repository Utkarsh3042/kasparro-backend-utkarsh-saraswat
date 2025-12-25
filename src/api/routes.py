from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime
from src.models.schemas import CryptoResponse, StatsResponse
from src.ingestion.coingecko import CoinGeckoSource
from src.ingestion.coinpaprika import CoinPaprikaSource
from src.database.storage import storage
from src.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/ingest/coingecko")
def ingest_coingecko(limit: int = Query(100, ge=1, le=250)):
    """Ingest data from CoinGecko API"""
    try:
        logger.info(f"Starting CoinGecko ingestion (limit={limit})")
        source = CoinGeckoSource()
        records = source.fetch_coins(limit=limit)
        
        if records:
            storage.add_records(records)
            return {
                "status": "success",
                "message": f"Ingested {len(records)} records from CoinGecko",
                "count": len(records)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch data")
    except Exception as e:
        logger.error(f"CoinGecko ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/coinpaprika")
def ingest_coinpaprika(limit: int = Query(50, ge=1, le=100)):
    """Ingest data from CoinPaprika API"""
    try:
        logger.info(f"Starting CoinPaprika ingestion (limit={limit})")
        source = CoinPaprikaSource()
        records = source.fetch_coins(limit=limit)
        
        if records:
            storage.add_records(records)
            return {
                "status": "success",
                "message": f"Ingested {len(records)} records from CoinPaprika",
                "count": len(records)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch data")
    except Exception as e:
        logger.error(f"CoinPaprika ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest/all")
def ingest_all():
    """Ingest data from both sources"""
    logger.info("Starting ingestion from all sources")
    
    results = {"coingecko": {}, "coinpaprika": {}}
    storage.clear()
    
    # CoinGecko
    try:
        cg_source = CoinGeckoSource()
        cg_records = cg_source.fetch_coins(limit=100)
        storage.add_records(cg_records)
        results["coingecko"] = {"status": "success", "count": len(cg_records)}
    except Exception as e:
        results["coingecko"] = {"status": "failed", "error": str(e)}
    
    # CoinPaprika
    try:
        cp_source = CoinPaprikaSource()
        cp_records = cp_source.fetch_coins(limit=50)
        storage.add_records(cp_records)
        results["coinpaprika"] = {"status": "success", "count": len(cp_records)}
    except Exception as e:
        results["coinpaprika"] = {"status": "failed", "error": str(e)}
    
    return {"status": "completed", "sources": results, "total_count": storage.get_count()}

@router.get("/data", response_model=CryptoResponse)
def get_data(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    source: Optional[str] = None,
    symbol: Optional[str] = None
):
    """Retrieve cryptocurrency data"""
    all_data = storage.get_all()
    
    if source:
        all_data = [d for d in all_data if d.source == source]
    
    if symbol:
        all_data = [d for d in all_data if d.symbol.upper() == symbol.upper()]
    
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
    """Get statistics"""
    all_data = storage.get_all()
    
    if not all_data:
        raise HTTPException(status_code=404, detail="No data available")
    
    valid_market_cap = [d.market_cap for d in all_data if d.market_cap]
    valid_volume = [d.total_volume for d in all_data if d.total_volume]
    valid_price = [d.current_price for d in all_data if d.current_price]
    
    coins_with_change = [d for d in all_data if d.price_change_percentage_24h is not None]
    sorted_by_change = sorted(coins_with_change, key=lambda x: x.price_change_percentage_24h, reverse=True)
    
    return StatsResponse(
        total_coins=len(all_data),
        total_market_cap=sum(valid_market_cap) if valid_market_cap else 0,
        total_volume=sum(valid_volume) if valid_volume else 0,
        avg_price=sum(valid_price) / len(valid_price) if valid_price else 0,
        top_gainers=sorted_by_change[:5],
        top_losers=sorted_by_change[-5:][::-1]
    )