import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from db.database import Base, get_db
from db.enums import CarStatus

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

def test_create_car():
    response = client.post("/cars", json={"model": "Toyota Camry", "year": 2023})
    assert response.status_code == 201
    data = response.json()
    assert data["model"] == "Toyota Camry"
    assert data["year"] == 2023
    assert data["status"] == CarStatus.AVAILABLE
    assert "id" in data

def test_get_cars_and_filter():
    # Create two cars
    client.post("/cars", json={"model": "Honda Civic", "year": 2022})
    car2_res = client.post("/cars", json={"model": "Ford F150", "year": 2021})
    
    # Update car2 to be IN_USE
    car2_id = car2_res.json()["id"]
    client.put(f"/cars/{car2_id}", json={"status": CarStatus.IN_USE})

    # Test get all
    res_all = client.get("/cars")
    assert res_all.status_code == 200
    assert len(res_all.json()) == 2

    # Test filter by status
    res_available = client.get(f"/cars?status={CarStatus.AVAILABLE.value}")
    assert res_available.status_code == 200
    assert len(res_available.json()) == 1
    assert res_available.json()[0]["model"] == "Honda Civic"

def test_update_car():
    res = client.post("/cars", json={"model": "Tesla Model 3", "year": 2024})
    car_id = res.json()["id"]

    update_res = client.put(f"/cars/{car_id}", json={"year": 2025})
    assert update_res.status_code == 200
    assert update_res.json()["year"] == 2025

def test_atomic_update_conflict():
    # Create a car
    res = client.post("/cars", json={"model": "Chevy Malibu", "year": 2020})
    car_id = res.json()["id"]

    # Attempt to change status to IN_USE, but provide wrong expected_status
    conflict_res = client.put(f"/cars/{car_id}", json={
        "status": CarStatus.IN_USE,
        "expected_status": CarStatus.IN_USE # Wrong! It should be AVAILABLE currently
    })
    
    assert conflict_res.status_code == 409
    assert "Race condition detected" in conflict_res.json()["detail"]

    # Now attempt with correct expected_status
    success_res = client.put(f"/cars/{car_id}", json={
        "status": CarStatus.IN_USE,
        "expected_status": CarStatus.AVAILABLE
    })
    
    assert success_res.status_code == 200
    assert success_res.json()["status"] == CarStatus.IN_USE

def test_update_non_existent_car():
    response = client.put("/cars/9999", json={"year": 2025})
    assert response.status_code == 404
    assert response.json()["detail"] == "Car not found"
