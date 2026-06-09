from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from routers import rentals
from utils.logger import get_logger
from config import settings
from db.database import SessionLocal
from db.models import Rental
from metrics import ONGOING_RENTALS
from datetime import datetime

logger = get_logger(settings.service_name, "main")

app = FastAPI(title="Rental Service API")

app.include_router(rentals.router)

instrumentator = Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
async def startup_event():
    logger.info("Rental Service is starting up...")
    db = SessionLocal()
    try:
        now = datetime.now()
        ongoing_rentals = db.query(Rental).filter(Rental.end_date > now).count()
        ONGOING_RENTALS.set(ongoing_rentals)
        logger.info(f"Initialized ONGOING_RENTALS metric to {ongoing_rentals}")
    except Exception as e:
        logger.error(f"Failed to initialize metrics: {e}")
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Rental Service is shutting down...")
