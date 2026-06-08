import httpx
from fastapi import Request, HTTPException
from fastapi.responses import Response
from config import settings
from logger import get_logger

logger = get_logger("router")

client = httpx.AsyncClient()

async def route_request(request: Request, path: str, explicit_body: bytes = None):
    if path.startswith("cars"):
        base_url = settings.vehicle_service_url
    elif path.startswith("rentals"):
        base_url = settings.rental_service_url
    elif path.startswith("returns"):
        base_url = settings.return_service_url
    else:
        raise HTTPException(status_code=404, detail="Route not found")

    target_url = f"{base_url}/{path}"
    
    query_string = request.url.query.encode("utf-8")
    if query_string:
        target_url = f"{target_url}?{query_string.decode('utf-8')}"

    headers = dict(request.headers)
    headers.pop("host", None)
    
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
