import time
import functools
from typing import Callable, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """Decorator for retrying functions with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            delay = base_delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {str(e)}")
                        raise
                    
                    wait_time = min(delay * (exponential_base ** (retries - 1)), max_delay)
                    logger.warning(f"{func.__name__} failed (attempt {retries}/{max_retries}), retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
            
            return None
        return wrapper
    return decorator