import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(app_env: str):
    logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    log_level = logging.INFO
    logger.setLevel(log_level)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    if app_env == "cloud":
        # Use structured JSON logging for GCP Cloud Run
        formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
        handler.setFormatter(formatter)
    else:
        # Use human readable formatting for local development
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        
    logger.addHandler(handler)
    
    # Suppress verbose loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
