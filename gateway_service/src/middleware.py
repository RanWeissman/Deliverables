import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from logger import get_logger

logger = get_logger("middleware")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        process_time_ms = (time.perf_counter() - start_time) * 1000
        
        path = request.url.path
        service_name = "Unknown Service"
        if path.startswith("/cars"):
            service_name = "Vehicle Service"
        elif path.startswith("/rentals"):
            service_name = "Rental Service"
        elif path.startswith("/returns"):
            service_name = "Return Service"
            
        logger.info(f"Proxied {request.method} {path} to {service_name} in {process_time_ms:.2f}ms.")
        
        return response
