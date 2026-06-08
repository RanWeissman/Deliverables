import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from src.main import app
from src.db.database import Base, get_db

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_future_rental_no_http_call():
    # Future dates -> Should NOT call Vehicle Service
    future_start = (datetime.now() + timedelta(days=5)).isoformat()
    future_end = (datetime.now() + timedelta(days=10)).isoformat()

    with patch("src.routers.rentals.httpx.Client") as mock_client:
        res = client.post("/rentals", json={
            "car_id": 1,
            "customer_name": "Alice",
            "start_date": future_start,
            "end_date": future_end
        })
        
        assert res.status_code == 201
        assert res.json()["customer_name"] == "Alice"
        
        # Verify httpx.Client was never initialized or used
        mock_client.assert_not_called()

def test_immediate_rental_calls_vehicle_service():
    # Past/Immediate dates -> SHOULD call Vehicle Service
    past_start = (datetime.now() - timedelta(hours=1)).isoformat()
    future_end = (datetime.now() + timedelta(days=2)).isoformat()

    with patch("src.routers.rentals.httpx.Client") as mock_client_cls:
        # Setup mock to simulate successful 200 OK from Vehicle Service
        mock_instance = mock_client_cls.return_value.__enter__.return_value
        mock_res = mock_instance.put.return_value
        mock_res.raise_for_status.return_value = None

        res = client.post("/rentals", json={
            "car_id": 2,
            "customer_name": "Bob",
            "start_date": past_start,
            "end_date": future_end
        })
        
        assert res.status_code == 201
        
        # Verify the PUT request was made
        mock_instance.put.assert_called_once_with("/cars/2", json={
            "status": "In use",
            "expected_status": "Available"
        })

def test_end_rental():
    future_start = (datetime.now() + timedelta(days=5)).isoformat()
    future_end = (datetime.now() + timedelta(days=10)).isoformat()

    res = client.post("/rentals", json={
        "car_id": 3,
        "customer_name": "Charlie",
        "start_date": future_start,
        "end_date": future_end
    })
    rental_id = res.json()["id"]

    end_res = client.put(f"/rentals/{rental_id}/end")
    assert end_res.status_code == 200
    assert end_res.json()["end_date"] < future_end
