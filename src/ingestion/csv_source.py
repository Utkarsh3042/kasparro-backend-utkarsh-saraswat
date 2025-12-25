import pandas as pd
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from src.models.schemas import CryptoData
from src.ingestion.base import BaseDataSource
from src.utils.logger import get_logger

class CSVDataSource(BaseDataSource):
    """CSV file data source for cryptocurrency data"""
    
    def __init__(self, csv_path: str = "data/crypto_data.csv"):
        super().__init__("CSV")
        self.csv_path = Path(csv_path)
        self.logger = get_logger(__name__)
    
    def fetch_coins(self, limit: int = 100) -> List[CryptoData]:
        """Fetch cryptocurrency data from CSV file"""
        try:
            if not self.csv_path.exists():
                self.logger.warning(f"CSV file not found: {self.csv_path}")
                return []
            
            self.logger.info(f"Reading data from CSV: {self.csv_path}")
            df = pd.read_csv(self.csv_path)
            
            if df.empty:
                self.logger.warning("CSV file is empty")
                return []
            
            # Take only the limit
            df = df.head(limit)
            
            crypto_list = []
            for _, row in df.iterrows():
                try:
                    crypto_data = self._parse_csv_row(row)
                    crypto_list.append(crypto_data)
                except Exception as e:
                    self.logger.warning(f"Failed to parse row: {e}")
                    continue
            
            self.log_success(len(crypto_list))
            return crypto_list
            
        except Exception as e:
            self.log_error(e)
            raise
    
    def _parse_csv_row(self, row: pd.Series) -> CryptoData:
        """Parse CSV row into CryptoData model"""
        return CryptoData(
            id=str(row.get('id', row.get('symbol', 'unknown'))).lower(),
            symbol=str(row.get('symbol', 'UNK')).upper(),
            name=str(row.get('name', 'Unknown')),
            current_price=self._safe_float(row.get('current_price')),
            market_cap=self._safe_float(row.get('market_cap')),
            total_volume=self._safe_float(row.get('total_volume')),
            price_change_24h=self._safe_float(row.get('price_change_24h')),
            price_change_percentage_24h=self._safe_float(row.get('price_change_percentage_24h')),
            last_updated=self._parse_datetime(row.get('last_updated')),
            source='csv'
        )
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        try:
            if pd.isna(value):
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_datetime(self, value) -> datetime:
        """Parse datetime from various formats"""
        try:
            if pd.isna(value):
                return datetime.now()
            return pd.to_datetime(value).to_pydatetime()
        except Exception:
            return datetime.now()
    
    def fetch_coin_by_id(self, coin_id: str) -> Optional[CryptoData]:
        """Fetch single coin from CSV by ID"""
        try:
            df = pd.read_csv(self.csv_path)
            row = df[df['id'] == coin_id].iloc[0]
            return self._parse_csv_row(row)
        except Exception:
            return None
