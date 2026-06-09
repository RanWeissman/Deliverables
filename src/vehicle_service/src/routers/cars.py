from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import update
from typing import List, Optional
import logging

from db.database import get_db
from db.models import Car
from db.enums import CarStatus
from schemas import CarCreate, CarUpdate, CarResponse
from metrics import ACTIVE_CARS

router = APIRouter(
    prefix="/cars",
    tags=["cars"],
)

logger = logging.getLogger("[VehicleService] routers.cars")

@router.post("", response_model=CarResponse, status_code=status.HTTP_201_CREATED)
def create_car(car: CarCreate, db: Session = Depends(get_db)):
    db_car = Car(model=car.model, year=car.year, status=CarStatus.AVAILABLE)
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    
    if db_car.status == CarStatus.AVAILABLE:
        ACTIVE_CARS.inc()
        
    logger.info(f"Created new car with id {db_car.id}")
    return db_car

@router.get("", response_model=List[CarResponse])
def get_cars(status: Optional[CarStatus] = None, db: Session = Depends(get_db)):
    query = db.query(Car)
    if status:
        query = query.filter(Car.status == status)
    cars = query.all()
    return cars

@router.get("/{id}", response_model=CarResponse)
def get_car(id: int, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car

@router.put("/{id}", response_model=CarResponse)
def update_car(id: int, car_update: CarUpdate, db: Session = Depends(get_db)):
    """
    Update a car's details or status.
    
    To prevent double-booking race conditions when updating the status, 
    clients can provide an `expected_status`. If provided alongside a new `status`, 
    this endpoint performs an atomic database update. If the car's current status 
    in the database does not match the `expected_status`, a 409 Conflict is raised.
    """
    # 1. Verification and Setup
    query = db.query(Car).filter(Car.id == id)
    db_car = query.first()
    
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")
        
    old_status = db_car.status
        
    # 2. Payload Extraction
    update_data = car_update.model_dump(exclude_unset=True)
    # Remove expected_status from the payload so SQLAlchemy doesn't try to save it
    expected_status = update_data.pop("expected_status", None)
    
    if not update_data:
        return db_car

    # 3. The Atomic Update (Concurrency Protection)
    if "status" in update_data and expected_status is not None:
        # Translates to: UPDATE cars SET ... WHERE id = :id AND status = :expected
        stmt = update(Car).where(
            Car.id == id,
            Car.status == expected_status
        ).values(**update_data)
        
        result = db.execute(stmt)
        # If 0 rows were updated, someone else already changed the status
        if result.rowcount == 0:
            logger.warning(f"Atomic update failed for car {id}. Expected status {expected_status} did not match.")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Race condition detected: Car status has changed since it was last read."
            )
        db.commit()
        logger.info(f"Car {id} updated atomically to status {update_data['status']}")
    
    # 4. Standard Update (Fallback)
    else:
        # Used for simple updates (like fixing a typo in 'year')
        query.update(update_data)
        db.commit()
        logger.info(f"Car {id} updated standardly")

    # 5. Finalization
    db.refresh(db_car)
    
    new_status = db_car.status
    if old_status != new_status:
        if new_status == CarStatus.AVAILABLE:
            ACTIVE_CARS.inc()
        elif old_status == CarStatus.AVAILABLE:
            ACTIVE_CARS.dec()
            
    return db_car

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_car(id: int, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    
    old_status = car.status
    db.delete(car)
    db.commit()
    
    if old_status == CarStatus.AVAILABLE:
        ACTIVE_CARS.dec()
        
    logger.info(f"Deleted car {id}")
    return None
