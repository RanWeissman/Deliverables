from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from routers import cars
from logger import get_logger

logger = get_logger("main")

app = FastAPI(title="Vehicle Service API")

app.include_router(cars.router)

instrumentator = Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
async def startup_event():
    logger.info("Vehicle Service is starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Vehicle Service is shutting down...")
