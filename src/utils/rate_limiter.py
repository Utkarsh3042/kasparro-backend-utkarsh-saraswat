import time
from typing import Callable, Optional
from datetime import datetime, timedelta
from collections import deque
from threading import Lock
from src.utils.logger import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """
    Token bucket rate limiter for API calls
    
    Allows burst requests up to max_calls, then enforces rate limit
    """
    
    def __init__(self, max_calls: int, time_window: int, name: str = "API"):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed in time window
            time_window: Time window in seconds
            name: Name for logging purposes
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.name = name
        self.calls = deque()
        self.lock = Lock()
        self.logger = get_logger(__name__)
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to apply rate limiting"""
        def wrapper(*args, **kwargs):
            self.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper
    
    def wait_if_needed(self):
        """Wait if rate limit is exceeded"""
        with self.lock:
            now = time.time()
            
            # Remove old calls outside time window
            while self.calls and self.calls[0] < now - self.time_window:
                self.calls.popleft()
            
            # Check if rate limit exceeded
            if len(self.calls) >= self.max_calls:
                sleep_time = self.time_window - (now - self.calls[0])
                if sleep_time > 0:
                    self.logger.warning(
                        f"⏱️  {self.name} rate limit reached "
                        f"({self.max_calls} calls/{self.time_window}s). "
                        f"Sleeping for {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    # Clean up old calls after sleep
                    now = time.time()
                    while self.calls and self.calls[0] < now - self.time_window:
                        self.calls.popleft()
            
            # Record this call
            self.calls.append(now)
            
            self.logger.debug(
                f"{self.name}: {len(self.calls)}/{self.max_calls} calls in window"
            )
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        with self.lock:
            now = time.time()
            # Clean up old calls
            while self.calls and self.calls[0] < now - self.time_window:
                self.calls.popleft()
            
            return {
                "name": self.name,
                "current_calls": len(self.calls),
                "max_calls": self.max_calls,
                "time_window": self.time_window,
                "available_calls": max(0, self.max_calls - len(self.calls)),
                "percentage_used": (len(self.calls) / self.max_calls) * 100
            }
    
    def reset(self):
        """Reset the rate limiter"""
        with self.lock:
            self.calls.clear()
            self.logger.info(f"🔄 {self.name} rate limiter reset")


class AdaptiveRateLimiter(RateLimiter):
    """
    Adaptive rate limiter that adjusts based on API responses
    
    Reduces rate when getting 429 (Too Many Requests) errors
    """
    
    def __init__(self, max_calls: int, time_window: int, name: str = "API"):
        super().__init__(max_calls, time_window, name)
        self.original_max_calls = max_calls
        self.backoff_factor = 0.5
        self.recovery_factor = 1.2
        self.min_calls = max(1, max_calls // 4)
    
    def on_rate_limit_error(self):
        """Called when API returns 429 error"""
        with self.lock:
            old_limit = self.max_calls
            self.max_calls = max(self.min_calls, int(self.max_calls * self.backoff_factor))
            
            self.logger.warning(
                f"⚠️  {self.name} hit rate limit! "
                f"Reducing max_calls: {old_limit} → {self.max_calls}"
            )
    
    def on_success(self):
        """Called on successful API call"""
        with self.lock:
            if self.max_calls < self.original_max_calls:
                old_limit = self.max_calls
                self.max_calls = min(
                    self.original_max_calls,
                    int(self.max_calls * self.recovery_factor)
                )
                
                if old_limit != self.max_calls:
                    self.logger.info(
                        f"✅ {self.name} recovering rate limit: "
                        f"{old_limit} → {self.max_calls}"
                    )