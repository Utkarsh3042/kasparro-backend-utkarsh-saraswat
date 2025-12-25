from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from src.api.routes import router
from src.database.storage import storage
from src.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Crypto ETL Backend System",
    description="ETL system for cryptocurrency data",
    version="1.0.0"
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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Crypto ETL Backend is running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "total_records": storage.get_count(),
            "last_updated": storage.last_updated.isoformat() if storage.last_updated else None
        }
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Crypto ETL Backend System Starting...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)