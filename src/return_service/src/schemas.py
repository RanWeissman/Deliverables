from pydantic import BaseModel

class ReturnRequest(BaseModel):
    rental_id: int
    car_id: int

class ReturnResponse(BaseModel):
    message: str
