from typing import List, Dict
from src.models.schemas import CryptoData
from src.utils.logger import get_logger

logger = get_logger(__name__)

def normalize_and_deduplicate(data: List[CryptoData]) -> List[CryptoData]:
    """
    Normalize and deduplicate cryptocurrency data from multiple sources
    
    Args:
        data: List of CryptoData objects from various sources
        
    Returns:
        List of deduplicated CryptoData objects
        
    Logic:
        1. Group data by canonical ID (symbol-based)
        2. For duplicates, prefer data in this order: coingecko > coinpaprika > csv
        3. Merge data fields, preferring non-null values
        4. Keep the most recent last_updated timestamp
    """
    if not data:
        return []
    
    logger.info(f"Starting normalization and deduplication for {len(data)} records")
    
    # Step 1: Create canonical IDs and group by them
    canonical_map: Dict[str, List[CryptoData]] = {}
    
    for crypto in data:
        # Create canonical ID (lowercase symbol as key)
        canonical_id = _create_canonical_id(crypto)
        
        if canonical_id not in canonical_map:
            canonical_map[canonical_id] = []
        
        canonical_map[canonical_id].append(crypto)
    
    # Step 2: Deduplicate and merge
    deduplicated_data = []
    
    for canonical_id, crypto_list in canonical_map.items():
        if len(crypto_list) == 1:
            # No duplicates, use as-is
            deduplicated_data.append(crypto_list[0])
        else:
            # Multiple sources for same crypto - merge them
            merged_crypto = _merge_crypto_data(crypto_list)
            deduplicated_data.append(merged_crypto)
            
            logger.debug(
                f"Merged {len(crypto_list)} records for {merged_crypto.symbol} "
                f"from sources: {[c.source for c in crypto_list]}"
            )
    
    logger.info(
        f"Normalization complete: {len(data)} raw records → "
        f"{len(deduplicated_data)} unique records "
        f"({len(data) - len(deduplicated_data)} duplicates removed)"
    )
    
    return deduplicated_data


def _create_canonical_id(crypto: CryptoData) -> str:
    """
    Create a canonical identifier for cryptocurrency
    
    Uses symbol as primary key (lowercase for consistency)
    Falls back to name if symbol is missing
    """
    if crypto.symbol:
        return crypto.symbol.lower().strip()
    elif crypto.name:
        return crypto.name.lower().strip().replace(' ', '-')
    else:
        # Fallback to id field
        return crypto.id.lower().strip()


def _merge_crypto_data(crypto_list: List[CryptoData]) -> CryptoData:
    """
    Merge multiple CryptoData objects for the same cryptocurrency
    
    Priority order: coingecko > coinpaprika > csv
    
    Strategy:
    - Use highest priority source's data as base
    - Fill in missing fields from lower priority sources
    - Use most recent last_updated timestamp
    """
    # Sort by priority (highest first)
    source_priority = {'coingecko': 3, 'coinpaprika': 2, 'csv': 1}
    sorted_list = sorted(
        crypto_list,
        key=lambda x: source_priority.get(x.source.lower(), 0),
        reverse=True
    )
    
    # Start with highest priority source as base
    base = sorted_list[0]
    
    # Create merged data
    merged = CryptoData(
        id=_get_best_value([c.id for c in sorted_list]),
        symbol=_get_best_value([c.symbol for c in sorted_list]),
        name=_get_best_value([c.name for c in sorted_list]),
        current_price=_get_best_numeric([c.current_price for c in sorted_list]),
        market_cap=_get_best_numeric([c.market_cap for c in sorted_list]),
        total_volume=_get_best_numeric([c.total_volume for c in sorted_list]),
        price_change_24h=_get_best_numeric([c.price_change_24h for c in sorted_list]),
        price_change_percentage_24h=_get_best_numeric([c.price_change_percentage_24h for c in sorted_list]),
        last_updated=max([c.last_updated for c in sorted_list]),  # Most recent
        source=f"merged({','.join([c.source for c in sorted_list])})"  # Track sources
    )
    
    return merged


def _get_best_value(values: List) -> str:
    """Get first non-null, non-empty string value from list"""
    for value in values:
        if value and str(value).strip():
            return str(value).strip()
    return values[0] if values else ""


def _get_best_numeric(values: List) -> float:
    """Get first non-null numeric value from list"""
    for value in values:
        if value is not None and value != 0:
            return value
    return values[0] if values else None


def normalize_symbol(symbol: str) -> str:
    """
    Normalize cryptocurrency symbol
    
    - Convert to uppercase
    - Remove whitespace
    - Remove special characters (keep alphanumeric and dash)
    """
    if not symbol:
        return ""
    
    # Convert to uppercase and strip
    normalized = symbol.upper().strip()
    
    # Remove special characters (keep alphanumeric and dash)
    normalized = ''.join(char for char in normalized if char.isalnum() or char == '-')
    
    return normalized


def normalize_name(name: str) -> str:
    """
    Normalize cryptocurrency name
    
    - Title case
    - Remove extra whitespace
    - Trim
    """
    if not name:
        return ""
    
    # Strip and normalize whitespace
    normalized = ' '.join(name.split())
    
    # Title case
    normalized = normalized.title()
    
    return normalized


def validate_crypto_data(crypto: CryptoData) -> bool:
    """
    Validate cryptocurrency data
    
    Returns True if data is valid, False otherwise
    """
    # Required fields
    if not crypto.symbol or not crypto.name:
        logger.warning(f"Missing required fields for {crypto.id}")
        return False
    
    # Symbol validation
    if len(crypto.symbol) > 10:
        logger.warning(f"Symbol too long: {crypto.symbol}")
        return False
    
    # Numeric validations
    if crypto.current_price is not None and crypto.current_price < 0:
        logger.warning(f"Negative price for {crypto.symbol}: {crypto.current_price}")
        return False
    
    if crypto.market_cap is not None and crypto.market_cap < 0:
        logger.warning(f"Negative market cap for {crypto.symbol}: {crypto.market_cap}")
        return False
    
    return True


def filter_valid_data(data: List[CryptoData]) -> List[CryptoData]:
    """
    Filter out invalid cryptocurrency data
    
    Args:
        data: List of CryptoData objects
        
    Returns:
        List of valid CryptoData objects
    """
    valid_data = [crypto for crypto in data if validate_crypto_data(crypto)]
    
    if len(valid_data) < len(data):
        logger.warning(
            f"Filtered out {len(data) - len(valid_data)} invalid records "
            f"({len(valid_data)}/{len(data)} valid)"
        )
    
    return valid_data


def get_deduplication_stats(original_count: int, deduplicated_count: int) -> Dict:
    """
    Get statistics about deduplication process
    
    Args:
        original_count: Number of records before deduplication
        deduplicated_count: Number of records after deduplication
        
    Returns:
        Dictionary with deduplication statistics
    """
    duplicates_removed = original_count - deduplicated_count
    duplicate_percentage = (duplicates_removed / original_count * 100) if original_count > 0 else 0
    
    return {
        'original_count': original_count,
        'deduplicated_count': deduplicated_count,
        'duplicates_removed': duplicates_removed,
        'duplicate_percentage': round(duplicate_percentage, 2),
        'efficiency': f"{100 - duplicate_percentage:.2f}%"
    }
