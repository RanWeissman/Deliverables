from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CarCreate(BaseModel):
    make: str
    model: str
    year: int
    status: str = "Available"

class CarUpdate(BaseModel):
    status: str
    expected_status: Optional[str] = None

class RentalCreate(BaseModel):
    car_id: int
    customer_id: int
    start_date: datetime
    end_date: datetime

class ReturnRequest(BaseModel):
    rental_id: int
    car_id: int
