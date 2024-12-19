import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from fastapi import HTTPException
from main import app, Session, create_db_and_tables, engine, get_session, Payment, PaymentDataJson
from sqlmodel import SQLModel, create_engine, Session as SQLSession
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


def test_create_payment(client, mock_session):
    """Test the POST /api/v1/payments endpoint."""
    payment_uid = uuid4()

    # Mock the payment object
    payment = Payment(
        payment_uid=payment_uid,
        status="completed",
        price=100.0
    )
    
    # Mock the database session commit
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()

    # Send request to create a payment
    response = client.post("/api/v1/payments", json={
        "payment_uid": str(payment_uid),
        "status": "completed",
        "price": 100.0
    })
    
    assert response.status_code == 201
    assert response.json()["payment_uid"] == str(payment_uid)
    assert response.json()["status"] == "completed"
    assert response.json()["price"] == 100.0


def test_create_payment_missing_field(client, mock_session):
    """Test creating a payment with missing fields."""
    # Send a request with missing `status` field
    response = client.post("/api/v1/payments", json={
        "payment_uid": str(uuid4()),
        "price": 100.0
    })

    assert response.status_code == 400
    assert "errors" in response.json()


def test_request_validation_error(client):
    """Test custom request validation exception handler."""
    # Send a request with invalid field (e.g., non-numeric price)
    response = client.post("/api/v1/payments", json={
        "payment_uid": str(uuid4()),
        "status": "completed",
        "price": "invalid_price"  # Invalid price type
    })
    
    assert response.status_code == 400
    assert "what" in response.json()
    assert "errors" in response.json()


