import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

@patch("router.client.request")
def test_proxy_forwards_cars_to_vehicle_service(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"success": true}'
    mock_response.headers = {}
    
    async def async_mock(*args, **kwargs):
        return mock_response
    mock_request.side_effect = async_mock

    response = client.get("/cars?status=Available")
    
    assert response.status_code == 200
    assert response.json() == {"success": True}
    
    mock_request.assert_called_once()
    kwargs = mock_request.call_args.kwargs
    assert kwargs["method"] == "GET"
    assert kwargs["url"].startswith("http://localhost:8001/cars")
    assert "status=Available" in kwargs["url"]

def test_proxy_404_on_unknown_route():
    response = client.get("/unknown_route")
    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found"
