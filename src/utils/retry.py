import time
import random
from typing import Callable, Optional, List, Type
from functools import wraps
from src.utils.logger import get_logger

logger = get_logger(__name__)

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff (2.0 = double each time)
        jitter: Add random jitter to prevent thundering herd
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Callback function called before each retry
    
    Example:
        @retry_with_backoff(max_retries=3, base_delay=2.0)
        def fetch_data():
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            
            while retries <= max_retries:
                try:
                    result = func(*args, **kwargs)
                    
                    # Log recovery if we had retries
                    if retries > 0:
                        logger.info(
                            f"✅ {func.__name__} succeeded after {retries} retries"
                        )
                    
                    return result
                
                except exceptions as e:
                    retries += 1
                    
                    if retries > max_retries:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries} retries. "
                            f"Last error: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (retries - 1)),
                        max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"⚠️  {func.__name__} attempt {retries}/{max_retries} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(retries, e)
                    
                    time.sleep(delay)
            
            return None
        
        return wrapper
    
    return decorator


def retry_on_status_codes(
    status_codes: List[int] = [429, 500, 502, 503, 504],
    max_retries: int = 3,
    base_delay: float = 1.0
):
    """
    Retry decorator specifically for HTTP status codes
    
    Args:
        status_codes: HTTP status codes to retry on
        max_retries: Maximum retry attempts
        base_delay: Initial delay between retries
    
    Example:
        @retry_on_status_codes(status_codes=[429, 503])
        def api_call():
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import requests
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except requests.HTTPError as e:
                    if e.response is None or e.response.status_code not in status_codes:
                        raise
                    
                    if attempt >= max_retries:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries} retries. "
                            f"Status: {e.response.status_code}"
                        )
                        raise
                    
                    # Special handling for 429 (Rate Limit)
                    if e.response.status_code == 429:
                        retry_after = e.response.headers.get('Retry-After')
                        if retry_after:
                            delay = float(retry_after)
                            logger.warning(
                                f"⏱️  Rate limited (429). "
                                f"Server says retry after {delay}s"
                            )
                        else:
                            delay = base_delay * (2 ** attempt)
                    else:
                        delay = base_delay * (2 ** attempt)
                    
                    logger.warning(
                        f"⚠️  HTTP {e.response.status_code} on attempt {attempt + 1}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
        
        return wrapper
    
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
        name: str = "API"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
        self.logger = get_logger(__name__)
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                    self.logger.info(
                        f"🔄 {self.name} circuit breaker: OPEN → HALF_OPEN (testing)"
                    )
                else:
                    raise Exception(
                        f"Circuit breaker OPEN for {self.name}. "
                        f"Service unavailable."
                    )
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery"""
        return (
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
            self.logger.info(
                f"✅ {self.name} circuit breaker: HALF_OPEN → CLOSED (recovered)"
            )
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            if self.state != "OPEN":
                self.state = "OPEN"
                self.logger.error(
                    f"❌ {self.name} circuit breaker: CLOSED → OPEN "
                    f"({self.failure_count} failures)"
                )
    
    def reset(self):
        """Manually reset the circuit breaker"""
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        self.logger.info(f"🔄 {self.name} circuit breaker manually reset")
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time
        }