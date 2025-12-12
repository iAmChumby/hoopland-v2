import logging
import os
from datetime import datetime

def setup_logger(mode: str, year: str = "") -> logging.Logger:
    """
    Configures the root logger to write to a mode-specific directory.
    Replaces any existing FileHandler to ensure clear separation of logs per run.
    
    Args:
        mode: The generation mode (e.g. 'NBA', 'NCAA', 'Draft', 'General')
        year: Optional year string to include in filename
    
    Returns:
        The configured root logger
    """
    # Create directory structure
    mode_clean = mode.upper() if mode else "MAX"
    log_dir = os.path.join("logs", mode_clean)
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    year_str = f"_{year}" if year else ""
    filename = f"{mode_clean}{year_str}_{timestamp}.log"
    filepath = os.path.join(log_dir, filename)
    
    # Configure Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing FileHandlers
    for h in root_logger.handlers[:]:
        if isinstance(h, logging.FileHandler):
            root_logger.removeHandler(h)
    
    # Add new FileHandler
    try:
        file_handler = logging.FileHandler(filepath, mode='w', encoding='utf-8')
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        root_logger.addHandler(file_handler)
        root_logger.info(f"Logging initialized. Writing to: {filepath}")
    except Exception as e:
        print(f"Failed to setup file logging: {e}")
        
    return root_logger
