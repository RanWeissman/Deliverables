from pydantic import BaseModel
from typing import Optional
from db.enums import CarStatus

class CarBase(BaseModel):
    model: str
    year: int

class CarCreate(CarBase):
    pass

class CarUpdate(BaseModel):
    model: Optional[str] = None
    year: Optional[int] = None
    status: Optional[CarStatus] = None
    expected_status: Optional[CarStatus] = None  # Crucial for atomic updates

class CarResponse(CarBase):
    id: int
    status: CarStatus

    model_config = {
        "from_attributes": True
    }
