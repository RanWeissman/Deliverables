import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app
from src.rabbitmq import process_return_event

client = TestClient(app)

@patch("routers.returns.publish_event")
def test_post_return_accepts_and_publishes(mock_publish):
    # Test that the API instantly accepts the request and publishes to RabbitMQ
    response = client.post("/returns", json={
        "rental_id": 42,
        "car_id": 10
    })
    
    assert response.status_code == 202
    assert response.json() == {"message": "Return request accepted and queued for processing"}
    mock_publish.assert_called_once_with(rental_id=42, car_id=10)

@patch("rabbitmq.httpx.Client")
def test_consumer_orchestrates_updates(mock_client_cls):
    # Setup mock to simulate successful 200 OK responses
    mock_instance = mock_client_cls.return_value.__enter__.return_value
    mock_res = mock_instance.put.return_value
    mock_res.raise_for_status.return_value = None

    # Mock the RabbitMQ Channel and Method objects
    mock_ch = MagicMock()
    mock_method = MagicMock()
    mock_method.delivery_tag = 1
    mock_properties = MagicMock()
    
    body = json.dumps({"rental_id": 99, "car_id": 5}).encode("utf-8")

    # Manually invoke the consumer callback
    process_return_event(mock_ch, mock_method, mock_properties, body)

    # Verify Rental Service was called to end the rental
    mock_instance.put.assert_any_call("/rentals/99/end")
    
    # Verify Vehicle Service was called to update fleet status
    mock_instance.put.assert_any_call("/cars/5", json={
        "status": "Available",
        "expected_status": "In use"
    })
    
    # Verify message was acknowledged
    mock_ch.basic_ack.assert_called_once_with(delivery_tag=1)
