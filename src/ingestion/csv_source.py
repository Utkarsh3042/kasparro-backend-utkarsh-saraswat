import pandas as pd
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from src.models.schemas import CryptoData
from src.ingestion.base import BaseDataSource
from src.utils.logger import get_logger

class CSVDataSource(BaseDataSource):
    """CSV file data source for cryptocurrency data with comprehensive error handling"""
    
    # Required columns for validation
    REQUIRED_COLUMNS = ['symbol', 'name']
    NUMERIC_COLUMNS = ['current_price', 'market_cap', 'total_volume', 
                       'price_change_24h', 'price_change_percentage_24h']
    MAX_FILE_SIZE_MB = 100  # Maximum file size in MB
    
    def __init__(self, csv_path: str = "data/crypto_data.csv"):
        super().__init__("CSV")
        self.csv_path = Path(csv_path)
        self.logger = get_logger(__name__)
        self.validation_errors = []
        self.error_summary = {
            'total_rows': 0,
            'valid_rows': 0,
            'invalid_rows': 0,
            'errors': []
        }
    
    def fetch_coins(self, limit: int = 100) -> List[CryptoData]:
        """Fetch cryptocurrency data from CSV file with comprehensive error handling"""
        self.validation_errors = []
        self.error_summary = {'total_rows': 0, 'valid_rows': 0, 'invalid_rows': 0, 'errors': []}
        
        try:
            # 1. Validate limit parameter
            if limit <= 0:
                self.logger.warning(f"Invalid limit: {limit}. Using default 100.")
                limit = 100
            
            # 2. Check if file exists
            if not self.csv_path.exists():
                self.logger.error(f"CSV file not found: {self.csv_path}")
                return []
            
            # 3. Check file size (prevent memory issues)
            file_size_mb = self.csv_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.MAX_FILE_SIZE_MB:
                self.logger.error(f"CSV file too large: {file_size_mb:.2f}MB (max: {self.MAX_FILE_SIZE_MB}MB)")
                return []
            
            # 4. Check file permissions
            if not self._check_file_readable():
                self.logger.error(f"Cannot read CSV file: {self.csv_path} (check permissions)")
                return []
            
            self.logger.info(f"Reading CSV file: {self.csv_path} ({file_size_mb:.2f}MB)")
            
            # 5. Read CSV with multiple error handling strategies
            df = self._read_csv_safely()
            if df is None:
                return []
            
            # 6. Validate DataFrame structure
            if not self._validate_dataframe(df):
                return []
            
            # 7. Process rows with limit
            self.error_summary['total_rows'] = len(df)
            df = df.head(limit)
            
            crypto_list = []
            for idx, row in df.iterrows():
                try:
                    crypto_data = self._parse_csv_row(row, row_num=idx+2)  # +2 for header and 0-index
                    crypto_list.append(crypto_data)
                    self.error_summary['valid_rows'] += 1
                except ValueError as e:
                    self.logger.warning(f"Row {idx+2}: Validation error - {e}")
                    self.validation_errors.append(f"Row {idx+2}: {e}")
                    self.error_summary['invalid_rows'] += 1
                    self.error_summary['errors'].append(str(e))
                    continue
                except Exception as e:
                    self.logger.warning(f"Row {idx+2}: Unexpected error - {e}")
                    self.error_summary['invalid_rows'] += 1
                    continue
            
            # 8. Log summary
            self._log_summary(crypto_list)
            
            return crypto_list
            
        except Exception as e:
            self.log_error(e)
            return []  # Return empty list instead of crashing
    
    def _check_file_readable(self) -> bool:
        """Check if file is readable"""
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                f.read(1)  # Try to read one character
            return True
        except PermissionError:
            return False
        except Exception:
            return False
    
    def _read_csv_safely(self) -> Optional[pd.DataFrame]:
        """Read CSV with comprehensive error handling"""
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                # Try to read with different error handling strategies
                df = pd.read_csv(
                    self.csv_path,
                    encoding=encoding,
                    on_bad_lines='skip',  # Skip malformed lines
                    engine='python',       # More flexible parser
                    encoding_errors='replace'  # Replace bad chars with �
                )
                
                if encoding != 'utf-8':
                    self.logger.warning(f"CSV read with {encoding} encoding (not UTF-8)")
                
                return df
                
            except pd.errors.ParserError as e:
                self.logger.error(f"CSV parsing error with {encoding}: {e}")
                if encoding == encodings[-1]:  # Last attempt
                    return None
                continue
                
            except UnicodeDecodeError as e:
                self.logger.warning(f"Encoding error with {encoding}: {e}")
                continue
                
            except pd.errors.EmptyDataError:
                self.logger.error("CSV file is empty or has no data")
                return None
                
            except Exception as e:
                self.logger.error(f"Unexpected error reading CSV: {e}")
                return None
        
        return None
    
    def _validate_dataframe(self, df: pd.DataFrame) -> bool:
        """Validate DataFrame structure and content"""
        # Check if empty
        if df.empty:
            self.logger.error("CSV file contains no data rows")
            return False
        
        # Check for required columns
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            self.logger.error(f"CSV missing required columns: {missing_cols}")
            self.logger.info(f"Available columns: {list(df.columns)}")
            return False
        
        # Check for duplicate column names
        if len(df.columns) != len(set(df.columns)):
            duplicates = [col for col in df.columns if list(df.columns).count(col) > 1]
            self.logger.warning(f"CSV has duplicate column names: {set(duplicates)}")
        
        # Check for completely empty columns
        empty_cols = [col for col in df.columns if df[col].isna().all()]
        if empty_cols:
            self.logger.warning(f"CSV has completely empty columns: {empty_cols}")
        
        # Warn about unexpected columns
        expected_cols = set(self.REQUIRED_COLUMNS + self.NUMERIC_COLUMNS + ['id', 'last_updated'])
        unexpected_cols = set(df.columns) - expected_cols
        if unexpected_cols:
            self.logger.info(f"CSV has additional columns (will be ignored): {unexpected_cols}")
        
        return True
    
    def _parse_csv_row(self, row: pd.Series, row_num: int = 0) -> CryptoData:
        """Parse CSV row with comprehensive validation"""
        # Validate required fields
        symbol = row.get('symbol')
        name = row.get('name')
        
        if pd.isna(symbol) or str(symbol).strip() == '':
            raise ValueError(f"Missing or empty 'symbol' field")
        
        if pd.isna(name) or str(name).strip() == '':
            raise ValueError(f"Missing or empty 'name' field")
        
        # Sanitize string fields
        symbol = str(symbol).strip().upper()
        name = str(name).strip()
        
        # Validate symbol format (alphanumeric only)
        if not symbol.replace('-', '').replace('_', '').isalnum():
            raise ValueError(f"Invalid symbol format: '{symbol}' (only alphanumeric allowed)")
        
        # Parse numeric fields with validation
        current_price = self._safe_float(
            row.get('current_price'),
            field_name='current_price',
            row_num=row_num,
            allow_negative=False
        )
        
        market_cap = self._safe_float(
            row.get('market_cap'),
            field_name='market_cap',
            row_num=row_num,
            allow_negative=False
        )
        
        total_volume = self._safe_float(
            row.get('total_volume'),
            field_name='total_volume',
            row_num=row_num,
            allow_negative=False
        )
        
        price_change_24h = self._safe_float(
            row.get('price_change_24h'),
            field_name='price_change_24h',
            row_num=row_num,
            allow_negative=True
        )
        
        price_change_percentage_24h = self._safe_float(
            row.get('price_change_percentage_24h'),
            field_name='price_change_percentage_24h',
            row_num=row_num,
            allow_negative=True
        )
        
        # Validate percentage range
        if price_change_percentage_24h is not None:
            if abs(price_change_percentage_24h) > 1000:  # More than 1000% change
                self.logger.warning(f"Row {row_num}: Suspicious price change: {price_change_percentage_24h}%")
        
        return CryptoData(
            id=str(row.get('id', symbol)).lower().strip(),
            symbol=symbol,
            name=name,
            current_price=current_price,
            market_cap=market_cap,
            total_volume=total_volume,
            price_change_24h=price_change_24h,
            price_change_percentage_24h=price_change_percentage_24h,
            last_updated=self._parse_datetime(row.get('last_updated')),
            source='csv'
        )
    
    def _safe_float(self, value, field_name: str = "field", row_num: int = 0, 
                    allow_negative: bool = False) -> Optional[float]:
        """Safely convert value to float with validation"""
        # Handle missing values
        if pd.isna(value) or value == '' or value is None:
            return None
        
        # Handle string cleaning (remove $, commas, etc.)
        if isinstance(value, str):
            value = value.strip().replace('$', '').replace(',', '').replace(' ', '')
            if value == '' or value.lower() in ['null', 'nan', 'none', 'n/a']:
                return None
        
        try:
            result = float(value)
            
            # Validate range
            if not allow_negative and result < 0:
                error_msg = f"{field_name}={result} is negative (not allowed)"
                self.logger.warning(f"Row {row_num}: {error_msg}")
                self.validation_errors.append(error_msg)
                return None
            
            # Check for infinity or NaN
            if not pd.notna(result) or result == float('inf') or result == float('-inf'):
                error_msg = f"{field_name}={value} is not a valid finite number"
                self.logger.warning(f"Row {row_num}: {error_msg}")
                return None
            
            return result
            
        except (ValueError, TypeError) as e:
            error_msg = f"{field_name}='{value}' is not a valid number (type: {type(value).__name__})"
            self.logger.warning(f"Row {row_num}: {error_msg}")
            self.validation_errors.append(error_msg)
            return None
    
    def _parse_datetime(self, value) -> datetime:
        """Parse datetime with multiple format support"""
        if pd.isna(value) or value == '' or value is None:
            return datetime.now()
        
        try:
            # Try pandas parser (handles many formats)
            return pd.to_datetime(value).to_pydatetime()
        except Exception:
            # Try common formats manually
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%m/%d/%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(str(value), fmt)
                except ValueError:
                    continue
            
            self.logger.debug(f"Could not parse datetime: {value}, using current time")
            return datetime.now()
    
    def _log_summary(self, crypto_list: List[CryptoData]):
        """Log processing summary"""
        if not crypto_list:
            self.logger.warning("❌ No valid data rows found in CSV")
            return
        
        self.logger.info("=" * 60)
        self.logger.info(f"✅ CSV Processing Complete:")
        self.logger.info(f"   Total rows in file: {self.error_summary['total_rows']}")
        self.logger.info(f"   Valid rows loaded: {len(crypto_list)}")
        self.logger.info(f"   Invalid rows skipped: {self.error_summary['invalid_rows']}")
        
        if self.validation_errors:
            self.logger.warning(f"⚠️  Found {len(self.validation_errors)} validation errors:")
            for i, error in enumerate(self.validation_errors[:5], 1):
                self.logger.warning(f"   {i}. {error}")
            if len(self.validation_errors) > 5:
                self.logger.warning(f"   ... and {len(self.validation_errors) - 5} more errors")
        
        self.logger.info("=" * 60)
        self.log_success(len(crypto_list))
    
    def fetch_coin_by_id(self, coin_id: str) -> Optional[CryptoData]:
        """Fetch single coin from CSV by ID"""
        try:
            if not self.csv_path.exists():
                self.logger.warning(f"CSV file not found: {self.csv_path}")
                return None
            
            df = self._read_csv_safely()
            if df is None:
                return None
            
            # Filter by ID (case-insensitive)
            filtered = df[df['id'].str.lower() == coin_id.lower()]
            
            if filtered.empty:
                self.logger.info(f"Coin with id '{coin_id}' not found in CSV")
                return None
            
            row = filtered.iloc[0]
            return self._parse_csv_row(row)
            
        except Exception as e:
            self.logger.error(f"Error fetching coin by ID '{coin_id}': {e}")
            return None
    
    def get_error_summary(self) -> dict:
        """Get detailed error summary from last fetch operation"""
        return self.error_summary
