from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = "sqlite:///./crypto_data.db"
    
    # API URLs
    coingecko_api_url: str = "https://api.coingecko.com/api/v3"
    coinpaprika_api_url: str = "https://api.coinpaprika.com/v1"
    
    # API Keys
    coinpaprika_api_key: str = ""
    
    # Rate Limiting
    coingecko_max_calls_per_minute: int = 50
    coinpaprika_max_calls_per_minute: int = 25
    
    # Retry Configuration
    max_retries: int = 3
    base_retry_delay: float = 2.0
    max_retry_delay: float = 60.0
    
    # Circuit Breaker
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    # Auto-ingestion
    auto_ingest_on_startup: bool = True
    auto_ingest_sources: Union[str, List[str]] = "csv,coingecko,coinpaprika"
    
    # Logging
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra='ignore'  # Ignore extra fields from .env that aren't in the model
    )
    
    @field_validator('auto_ingest_sources', mode='before')
    @classmethod
    def parse_sources(cls, v):
        """Parse comma-separated string into list"""
        if isinstance(v, str):
            return [x.strip() for x in v.split(',') if x.strip()]
        elif isinstance(v, list):
            return v
        return ["csv", "coingecko", "coinpaprika"]

_settings = None

def get_settings() -> Settings:
    """Get cached settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings