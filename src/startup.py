import asyncio
import os
from src.utils.logger import get_logger
from src.database.storage import storage

logger = get_logger(__name__)

async def auto_ingest_on_startup():
    """Auto-ingest data on application startup"""
    auto_ingest = os.getenv('AUTO_INGEST_ON_STARTUP', 'false').lower() == 'true'
    
    if not auto_ingest:
        logger.info("Auto-ingest disabled")
        return
    
    sources_str = os.getenv('AUTO_INGEST_SOURCES', 'csv,coingecko,coinpaprika')
    sources = [s.strip() for s in sources_str.split(',')]
    
    logger.info(f"🚀 Starting auto-ingest from sources: {sources}")
    
    all_records = []
    
    # CSV Source
    if 'csv' in sources:
        try:
            from src.ingestion.csv_source import CSVDataSource
            csv_source = CSVDataSource()
            csv_records = csv_source.fetch_coins(limit=100)
            all_records.extend(csv_records)
            logger.info(f"✅ Auto-ingested {len(csv_records)} records from CSV")
        except Exception as e:
            logger.error(f"❌ CSV auto-ingest failed: {e}")
    
    # CoinGecko Source
    if 'coingecko' in sources:
        try:
            from src.ingestion.coingecko import CoinGeckoSource
            cg_source = CoinGeckoSource()
            cg_records = cg_source.fetch_coins(limit=100)
            all_records.extend(cg_records)
            logger.info(f"✅ Auto-ingested {len(cg_records)} records from CoinGecko")
        except Exception as e:
            logger.error(f"❌ CoinGecko auto-ingest failed: {e}")
    
    # CoinPaprika Source
    if 'coinpaprika' in sources:
        try:
            from src.ingestion.coinpaprika import CoinPaprikaSource
            cp_source = CoinPaprikaSource()
            cp_records = cp_source.fetch_coins(limit=50)
            all_records.extend(cp_records)
            logger.info(f"✅ Auto-ingested {len(cp_records)} records from CoinPaprika")
        except Exception as e:
            logger.error(f"❌ CoinPaprika auto-ingest failed: {e}")
    
    # Store normalized and deduplicated data
    if all_records:
        storage.add_records(all_records, normalize=True)
        logger.info(f"🎉 Auto-ingest completed: {storage.get_count()} unique coins stored")
    else:
        logger.warning("⚠️  No records were ingested from any source")
