from fastapi import APIRouter, HTTPException, status
from schemas import ReturnRequest, ReturnResponse
from rabbitmq import publish_event
from logger import get_logger

router = APIRouter(
    prefix="/returns",
    tags=["returns"]
)

logger = get_logger("routers.returns")

@router.post("", response_model=ReturnResponse, status_code=status.HTTP_202_ACCEPTED)
def request_return(req: ReturnRequest):
    try:
        publish_event(rental_id=req.rental_id, car_id=req.car_id)
        logger.info(f"API received return request, published Event for rental {req.rental_id}")
        return {"message": "Return request accepted and queued for processing"}
    except Exception as e:
        logger.error(f"API failed to queue return request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to queue return request")
