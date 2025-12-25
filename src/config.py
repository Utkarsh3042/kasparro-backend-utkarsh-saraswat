from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    coinpaprika_api_key: str
    coinpaprika_api_url: str = "https://api.coinpaprika.com/v1"
    coingecko_api_url: str = "https://api.coingecko.com/api/v3"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()