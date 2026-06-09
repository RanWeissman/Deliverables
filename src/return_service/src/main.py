import threading
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from routers import returns
from rabbitmq import consume_events
from logger import get_logger

logger = get_logger("main")

app = FastAPI(title="Return Service API")

app.include_router(returns.router)

instrumentator = Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
async def startup_event():
    logger.info("Return Service is starting up...")
    # Start RabbitMQ consumer in a background thread
    consumer_thread = threading.Thread(target=consume_events, daemon=True)
    consumer_thread.start()
    logger.info("Background Consumer Thread started.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Return Service is shutting down...")
