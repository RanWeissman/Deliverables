from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator
from typing import Optional

from router import route_request
from middleware import LoggingMiddleware
from logger import get_logger
from schemas import CarCreate, CarUpdate, RentalCreate, ReturnRequest

logger = get_logger("main")

app = FastAPI(title="DriveNow API Gateway")

app.add_middleware(LoggingMiddleware)

instrumentator = Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
async def startup_event():
    logger.info("API Gateway is starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("API Gateway is shutting down...")


# --- Explicit Routes for OpenAPI Documentation ---

@app.post("/cars", tags=["Cars"])
async def add_new_car(request: Request, payload: CarCreate):
    return await route_request(request, "cars", explicit_body=payload.model_dump_json().encode('utf-8'))

@app.put("/cars/{car_id}", tags=["Cars"])
async def update_car(request: Request, car_id: int, payload: CarUpdate):
    return await route_request(request, f"cars/{car_id}", explicit_body=payload.model_dump_json().encode('utf-8'))

@app.get("/cars", tags=["Cars"])
async def list_cars(request: Request, status: Optional[str] = None):
    return await route_request(request, "cars")

@app.post("/rentals", tags=["Rentals"])
async def register_rental(request: Request, payload: RentalCreate):
    return await route_request(request, "rentals", explicit_body=payload.model_dump_json().encode('utf-8'))

@app.post("/returns", tags=["Returns"])
async def end_rental(request: Request, payload: ReturnRequest):
    return await route_request(request, "returns", explicit_body=payload.model_dump_json().encode('utf-8'))

# Fallback catch-all for any other routes
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False)
async def catch_all(request: Request, path: str):
    return await route_request(request, path)
