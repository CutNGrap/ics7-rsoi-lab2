import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from fastapi import HTTPException
from main import app, Session, create_db_and_tables, engine, get_session, Car, CarDataJson, CarReserveResponse
from sqlmodel import SQLModel, create_engine, Session as SQLSession

# Mock the session to avoid using a real database
from unittest.mock import MagicMock

@pytest.fixture(scope="module")
def client():
    """
    Create a FastAPI TestClient for testing the endpoints.
    """
    # Mock database connection
    create_db_and_tables()  # This would create tables in an in-memory DB if configured
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_session():
    """
    Fixture to mock the session dependency for the endpoints.
    """
    mock_session = MagicMock(spec=SQLSession)
    return mock_session


def test_health(client):
    """Test the health check endpoint."""
    response = client.get("/manage/health")
    assert response.status_code == 200
    assert response.json() == {}  # No content in the health endpoint


def test_get_all_cars(client, mock_session):
    """Test the GET /api/v1/cars endpoint."""
    # Mocking a car object
    car = Car(
        car_uid=uuid4(),
        brand="Toyota",
        model="Corolla",
        registration_number="ABC123",
        power=100,
        price=20000,
        type="sedan",
        availability=True
    )
    mock_session.exec.return_value.all.return_value = [car]
    
    # Mock the session dependency
    response = client.get("/api/v1/cars?page=1&size=1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["brand"] == "Toyota"


def test_reserve_car(client, mock_session):
    """Test the PUT /api/v1/cars/{car_uid}/reserve endpoint."""
    car_uid = uuid4()

    # Mock the car object
    car = Car(
        car_uid=car_uid,
        brand="Honda",
        model="Civic",
        registration_number="XYZ123",
        power=120,
        price=25000,
        type="sedan",
        availability=True
    )
    mock_session.exec.return_value.first.return_value = car
    
    # Mock the update operation
    mock_session.commit = MagicMock()
    
    # Send request to reserve the car
    response = client.put(f"/api/v1/cars/{car_uid}/reserve")
    assert response.status_code == 200
    assert response.json()["message"] == "Car reserved successfully"
    assert not response.json()["availability"]  # Car should be reserved (availability = False)


def test_release_car(client, mock_session):
    """Test the PUT /api/v1/cars/{car_uid}/release endpoint."""
    car_uid = uuid4()

    # Mock the car object
    car = Car(
        car_uid=car_uid,
        brand="Tesla",
        model="Model S",
        registration_number="TES123",
        power=300,
        price=50000,
        type="sedan",
        availability=False  # Initially reserved
    )
    mock_session.exec.return_value.first.return_value = car
    
    # Mock the update operation
    mock_session.commit = MagicMock()
    
    # Send request to release the car
    response = client.put(f"/api/v1/cars/{car_uid}/release")
    assert response.status_code == 200
    assert response.json()["message"] == "Car released successfully"
    assert response.json()["availability"]  # Car should be available (availability = True)


def test_reserve_car_not_found(client, mock_session):
    """Test reserving a car that doesn't exist."""
    car_uid = uuid4()

    # Mock the database returning None for the car (not found)
    mock_session.exec.return_value.first.return_value = None
    
    # Send request to reserve the car
    response = client.put(f"/api/v1/cars/{car_uid}/reserve")
    assert response.status_code == 404
    assert response.json()["detail"] == "Car not found"


def test_reserve_car_already_reserved(client, mock_session):
    """Test trying to reserve an already reserved car."""
    car_uid = uuid4()

    # Mock the car object with availability set to False (already reserved)
    car = Car(
        car_uid=car_uid,
        brand="BMW",
        model="X5",
        registration_number="BMW123",
        power=250,
        price=60000,
        type="SUV",
        availability=False  # Car already reserved
    )
    mock_session.exec.return_value.first.return_value = car
    
    # Send request to reserve the car
    response = client.put(f"/api/v1/cars/{car_uid}/reserve")
    assert response.status_code == 400
    assert response.json()["detail"] == "Car is already reserved"


def test_request_validation_error(client):
    """Test custom request validation exception handler."""
    response = client.get("/api/v1/cars?page=0")  # page should be >= 1
    assert response.status_code == 400
    assert "what" in response.json()
    assert "errors" in response.json()
