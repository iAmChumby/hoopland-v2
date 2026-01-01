import time
import functools
import logging
import requests

logger = logging.getLogger(__name__)


class CircuitBreaker:
    def __init__(self, failure_threshold=3, reset_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure_time = 0
        self.is_open = False

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            if not self.is_open:
                logger.warning(
                    f"Circuit breaker opened after {self.failure_count} consecutive failures. "
                    f"Skipping API calls for {self.reset_timeout}s."
                )
            self.is_open = True

    def record_success(self):
        self.failure_count = 0
        self.is_open = False

    def should_allow_request(self):
        if not self.is_open:
            return True
        if time.time() - self.last_failure_time >= self.reset_timeout:
            logger.info("Circuit breaker reset. Allowing API calls again.")
            self.is_open = False
            self.failure_count = 0
            return True
        return False


circuit_breaker = CircuitBreaker()

def retry_api_call(max_retries=3, initial_backoff=10.0, backoff_factor=1.5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not circuit_breaker.should_allow_request():
                logger.debug(f"Circuit breaker open, skipping {func.__name__}")
                raise ConnectionError("Circuit breaker is open - API unavailable")

            retries = 0
            backoff = initial_backoff

            while retries <= max_retries:
                try:
                    result = func(*args, **kwargs)
                    if result is None:
                        raise ValueError("API returned None (likely non-200 status)")
                    circuit_breaker.record_success()
                    return result
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        circuit_breaker.record_failure()
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries. Error: {e}")
                        raise e
                    logger.warning(f"Function {func.__name__} failed (Attempt {retries}/{max_retries}). Retrying in {backoff:.2f}s... Error: {e}")
                    time.sleep(backoff)
                    backoff *= backoff_factor
            return None
        return wrapper
    return decorator
