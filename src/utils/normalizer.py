from typing import Dict, Optional, List
from src.models.schemas import CryptoData
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DataNormalizer:
    """Normalizes cryptocurrency data across different sources"""
    
    # Symbol-based canonical ID mapping
    CANONICAL_MAPPINGS: Dict[str, str] = {
        'BTC': 'btc',
        'ETH': 'eth',
        'USDT': 'usdt',
        'BNB': 'bnb',
        'SOL': 'sol',
        'XRP': 'xrp',
        'ADA': 'ada',
        'DOGE': 'doge',
        'DOT': 'dot',
        'MATIC': 'matic',
        'AVAX': 'avax',
        'LINK': 'link',
        'UNI': 'uni',
        'ATOM': 'atom',
        'LTC': 'ltc',
    }
    
    # Known aliases
    SYMBOL_ALIASES: Dict[str, str] = {
        'WBTC': 'BTC',
        'WETH': 'ETH',
    }
    
    @classmethod
    def normalize(cls, crypto: CryptoData) -> CryptoData:
        """
        Normalize cryptocurrency data by assigning canonical ID
        
        Strategy:
        1. Check symbol-based mapping
        2. Check source ID mapping
        3. Fallback to symbol-based ID
        """
        # Normalize symbol
        symbol = crypto.symbol.upper()
        
        # Check for aliases
        if symbol in cls.SYMBOL_ALIASES:
            symbol = cls.SYMBOL_ALIASES[symbol]
        
        # Assign canonical ID
        if symbol in cls.CANONICAL_MAPPINGS:
            canonical_id = cls.CANONICAL_MAPPINGS[symbol]
        else:
            # Create canonical ID from symbol
            canonical_id = symbol.lower()
        
        # Update crypto data
        crypto.canonical_id = canonical_id
        
        logger.debug(f"Normalized {crypto.source}:{crypto.id} -> canonical:{canonical_id}")
        
        return crypto
    
    @classmethod
    def deduplicate(cls, crypto_list: List[CryptoData]) -> List[CryptoData]:
        """
        Deduplicate cryptocurrency data by canonical ID
        Priority: coingecko > coinpaprika > csv
        """
        source_priority = {'coingecko': 3, 'coinpaprika': 2, 'csv': 1}
        
        canonical_map: Dict[str, CryptoData] = {}
        
        for crypto in crypto_list:
            # Normalize first
            crypto = cls.normalize(crypto)
            
            canonical = crypto.canonical_id or crypto.symbol.lower()
            
            # Check if we already have this coin
            if canonical in canonical_map:
                existing = canonical_map[canonical]
                
                # Compare priorities
                existing_priority = source_priority.get(existing.source, 0)
                new_priority = source_priority.get(crypto.source, 0)
                
                # Keep higher priority source
                if new_priority > existing_priority:
                    canonical_map[canonical] = crypto
                    logger.debug(f"Replaced {canonical}: {existing.source} -> {crypto.source}")
            else:
                canonical_map[canonical] = crypto
        
        deduplicated = list(canonical_map.values())
        logger.info(f"Deduplicated {len(crypto_list)} records -> {len(deduplicated)} unique coins")
        
        return deduplicated
