from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from src.api.routes import router
from src.database.storage import storage
from src.database.connection import init_db  # Add this
from src.utils.logger import get_logger
from src.startup import auto_ingest_on_startup

logger = get_logger(__name__)

app = FastAPI(
    title="Crypto ETL Backend System",
    description="Production-ready ETL system with CSV, CoinGecko, and CoinPaprika data sources. Features normalization, deduplication, auto-ingestion, and ORM with PostgreSQL.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["crypto"])

@app.get("/health")
def health_check():
    """
    Comprehensive health check endpoint
    Returns system status, data statistics, and enabled features
    """
    try:
        data_count = storage.get_count()
        last_updated = storage.last_updated
        
        return {
            "status": "healthy",
            "message": "Crypto ETL Backend is running",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "connected": True,
                "total_records": data_count,
                "last_updated": last_updated.isoformat() if last_updated else None
            },
            "features": {
                "csv_ingestion": True,
                "api_ingestion": True,
                "normalization": True,
                "deduplication": True,
                "auto_ingest": True,
                "multi_source": True,
                "orm": True,
                "postgresql": True
            },
            "sources": ["csv", "coingecko", "coinpaprika"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("=" * 70)
    logger.info("🚀 Crypto ETL Backend System Starting...")
    logger.info("📦 Version: 2.0.0")
    logger.info("✨ Features: CSV + API Ingestion, Normalization, Auto-Start ETL, ORM")
    logger.info("🔗 Sources: CSV, CoinGecko, CoinPaprika")
    logger.info("🗄️  Database: PostgreSQL with SQLAlchemy ORM")
    logger.info("=" * 70)
    
    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Auto-ingest data on startup
    await auto_ingest_on_startup()

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("🛑 Crypto ETL Backend System Shutting Down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)