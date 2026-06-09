from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from routers import rentals
from logger import get_logger

logger = get_logger("main")

app = FastAPI(title="Rental Service API")

app.include_router(rentals.router)

instrumentator = Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
async def startup_event():
    logger.info("Rental Service is starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Rental Service is shutting down...")
