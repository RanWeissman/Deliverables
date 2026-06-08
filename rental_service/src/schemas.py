from pydantic import BaseModel
from datetime import datetime

class RentalBase(BaseModel):
    car_id: int
    customer_name: str
    start_date: datetime
    end_date: datetime

class RentalCreate(RentalBase):
    pass

class RentalResponse(RentalBase):
    id: int

    model_config = {
        "from_attributes": True
    }
