import httpx
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db.database import get_db
from db.models import Rental
from schemas import RentalCreate, RentalResponse
from config import settings

router = APIRouter(
    prefix="/rentals",
    tags=["rentals"],
)

logger = logging.getLogger("[RentalService] routers.rentals")

@router.post("", response_model=RentalResponse, status_code=status.HTTP_201_CREATED)
def create_rental(rental: RentalCreate, db: Session = Depends(get_db)):
    if rental.end_date <= rental.start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    # 1. Attempt to create rental in database
    db_rental = Rental(**rental.model_dump())
    db.add(db_rental)
    
    try:
        db.commit()
        db.refresh(db_rental)
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Double booking attempt detected for car {rental.car_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Car is already booked for these dates")

    # 2. Check if this is an immediate rental
    # Use timezone aware comparison if possible, fallback to naive depending on payload
    now = datetime.now(timezone.utc) if rental.start_date.tzinfo else datetime.now()
    is_immediate = rental.start_date <= now
    
    if is_immediate:
        logger.info(f"Immediate rental detected for car {rental.car_id}. Contacting Vehicle Service...")
        try:
            with httpx.Client(base_url=settings.vehicle_service_url) as client:
                res = client.put(f"/cars/{rental.car_id}", json={
                    "status": "In use",
                    "expected_status": "Available"
                })
                res.raise_for_status()
                logger.info(f"Successfully updated car {rental.car_id} status to 'In use'")
        except httpx.HTTPStatusError as exc:
            logger.error(f"Failed to update car status. HTTP Error: {exc.response.status_code} - {exc.response.text}")
            db.delete(db_rental)
            db.commit()
            if exc.response.status_code == 409:
                raise HTTPException(status_code=409, detail="Race condition: Car was just rented by someone else.")
            raise HTTPException(status_code=500, detail="Failed to communicate with Vehicle Service.")
        except httpx.RequestError as exc:
            logger.error(f"Vehicle Service is unreachable: {str(exc)}")
            db.delete(db_rental)
            db.commit()
            raise HTTPException(status_code=503, detail="Vehicle Service unavailable. Rental rolled back.")
    else:
        logger.info(f"Future rental created for car {rental.car_id}. Skipping Vehicle Service API call.")

    return db_rental

@router.put("/{id}/end", response_model=RentalResponse)
def end_rental(id: int, db: Session = Depends(get_db)):
    db_rental = db.query(Rental).filter(Rental.id == id).first()
    if not db_rental:
        raise HTTPException(status_code=404, detail="Rental not found")
        
    db_rental.end_date = datetime.now()
    db.commit()
    db.refresh(db_rental)
    
    logger.info(f"Rental {id} ended.")
    return db_rental
