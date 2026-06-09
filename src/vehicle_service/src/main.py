from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from routers import cars
from logger import get_logger
from db.database import SessionLocal
from db.models import Car
from db.enums import CarStatus
from metrics import ACTIVE_CARS

logger = get_logger("main")

app = FastAPI(title="Vehicle Service API")

app.include_router(cars.router)

instrumentator = Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
async def startup_event():
    logger.info("Vehicle Service is starting up...")
    db = SessionLocal()
    try:
        available_cars = db.query(Car).filter(Car.status == CarStatus.AVAILABLE).count()
        ACTIVE_CARS.set(available_cars)
        logger.info(f"Initialized ACTIVE_CARS metric to {available_cars}")
    except Exception as e:
        logger.error(f"Failed to initialize metrics: {e}")
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Vehicle Service is shutting down...")
