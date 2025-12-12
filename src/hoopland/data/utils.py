import time
import functools
import logging
import requests

logger = logging.getLogger(__name__)

def retry_api_call(max_retries=3, initial_backoff=10.0, backoff_factor=1.5):
    """
    Decorator to retry a function call upon raising an exception or returning None/failures.
    
    :param max_retries: Maximum number of retries before giving up.
    :param initial_backoff: Initial sleep time in seconds.
    :param backoff_factor: Multiplier for sleep time after each failure.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            backoff = initial_backoff
            
            while retries <= max_retries:
                try:
                    result = func(*args, **kwargs)
                    # For requests based functions, we might want to check for None or specific errors if they swallow them
                    # But assuming the function raises exceptions on real failure, or returns None if we want to retry on None?
                    # The clients currently return empty structs or None on failure often. 
                    # Let's assume exceptions are the primary trigger, but we could also inspect result?
                    # Based on existing code, clients catch exceptions and return None/Empty. 
                    # We might need to modify clients to RAISE exceptions so this wrapper can catch them, 
                    # OR we check if result is None/Empty.
                    # LET'S CHECK:
                    # NBA Client methods often return DataFrames or generic objects. If they fail inside, they likely crash (nba_api does).
                    # ESPN Client returns None on non-200.
                    
                    if result is None:
                         raise ValueError("API returned None (likely non-200 status)")
                         
                    return result
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries. Error: {e}")
                        raise e # Re-raise the last exception
                    
                    logger.warning(f"Function {func.__name__} failed (Attempt {retries}/{max_retries}). Retrying in {backoff:.2f}s... Error: {e}")
                    time.sleep(backoff)
                    backoff *= backoff_factor
            return None
        return wrapper
    return decorator
