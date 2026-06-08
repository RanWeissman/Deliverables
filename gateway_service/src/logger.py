import logging
import sys
from .config import settings

def get_logger(name: str | None = None) -> logging.Logger:
    logger_name = f"[{settings.service_name}]"
    if name:
        logger_name = f"{logger_name} {name}"
        
    logger = logging.getLogger(logger_name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(name)s %(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # StreamHandler for stdout
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        # FileHandler for app.log
        file_handler = logging.FileHandler("app.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger
