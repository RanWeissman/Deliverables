import httpx
from fastapi import Request, HTTPException
from fastapi.responses import Response
from config import settings
import json
from utils.logger import get_logger
from config import settings
from utils.schemas import ReturnRequest
from rabbitmq import publish_event

logger = get_logger(settings.service_name, "router")

client = httpx.AsyncClient()

async def route_request(request: Request, path: str, explicit_body: bytes = None):
    if path.startswith("returns"):
        body = explicit_body if explicit_body is not None else await request.body()
        try:
            req_data = ReturnRequest.model_validate_json(body)
            publish_event(rental_id=req_data.rental_id, car_id=req_data.car_id)
            logger.info(f"Gateway received return request, published Event for rental {req_data.rental_id}")
            return Response(
                content=json.dumps({"message": "Return request accepted and queued for processing"}),
                status_code=202,
                media_type="application/json"
            )
        except Exception as e:
            logger.error(f"API failed to queue return request: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to queue return request")

    if path.startswith("cars"):
        base_url = settings.vehicle_service_url
    elif path.startswith("rentals"):
        base_url = settings.rental_service_url
    else:
        raise HTTPException(status_code=404, detail="Route not found")

    target_url = f"{base_url}/{path}"
    
    query_string = request.url.query.encode("utf-8")
    if query_string:
        target_url = f"{target_url}?{query_string.decode('utf-8')}"

    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    body = explicit_body if explicit_body is not None else await request.body()
    
    try:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body
        )
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except httpx.RequestError as e:
        logger.error(f"Failed to route request to {target_url}: {str(e)}")
        raise HTTPException(status_code=502, detail="Bad Gateway: Downstream service is unreachable.")
