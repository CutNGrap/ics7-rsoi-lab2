import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from fastapi import HTTPException
from main import app, Session, Rental, RentalDataJson
from unittest.mock import MagicMock
from datetime import datetime


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


def test_get_user_rentals(client, mock_session):
    """Test the GET /api/v1/rental endpoint to fetch user rentals."""
    username = "testuser"

    # Mock the rental data
    rental = Rental(
        rental_uid=uuid4(),
        username=username,
        payment_uid=uuid4(),
        car_uid=uuid4(),
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 1, 10),
        status="IN_PROGRESS"
    )

    mock_session.exec.return_value.all.return_value = [rental]

    # Send request to fetch rentals
    response = client.get("/api/v1/rental", headers={"X-User-Name": username})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["username"] == username


def test_get_rental_details(client, mock_session):
    """Test the GET /api/v1/rental/{rentalUid} endpoint to fetch rental details."""
    rental_uid = uuid4()
    username = "testuser"

    # Mock the rental data
    rental = Rental(
        rental_uid=rental_uid,
        username=username,
        payment_uid=uuid4(),
        car_uid=uuid4(),
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 1, 10),
        status="IN_PROGRESS"
    )

    mock_session.exec.return_value.first.return_value = rental

    # Send request to fetch rental details
    response = client.get(f"/api/v1/rental/{rental_uid}", headers={"X-User-Name": username})

    assert response.status_code == 200
    assert response.json()["rental_uid"] == str(rental_uid)
    assert response.json()["username"] == username


def test_create_rental(client, mock_session):
    """Test the POST /api/v1/rentals endpoint to create a rental."""
    rental_uid = uuid4()

    # Mock the rental data
    rental = Rental(
        rental_uid=rental_uid,
        username="testuser",
        payment_uid=uuid4(),
        car_uid=uuid4(),
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 1, 10),
        status="IN_PROGRESS"
    )

    # Mock the database session commit
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()

    # Send request to create a rental
    response = client.post("/api/v1/rentals", json={
        "rental_uid": str(rental_uid),
        "username": "testuser",
        "payment_uid": str(rental.payment_uid),
        "car_uid": str(rental.car_uid),
        "date_from": rental.date_from.isoformat(),
        "date_to": rental.date_to.isoformat(),
        "status": "IN_PROGRESS"
    })

    assert response.status_code == 201
    assert response.json()["rental_uid"] == str(rental_uid)
    assert response.json()["status"] == "IN_PROGRESS"


def test_cancel_rental(client, mock_session):
    """Test the PUT /api/v1/rentals/{rental_uid}/cancel endpoint."""
    rental_uid = uuid4()
    username = "testuser"

    # Mock the rental data
    rental = Rental(
        rental_uid=rental_uid,
        username=username,
        payment_uid=uuid4(),
        car_uid=uuid4(),
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 1, 10),
        status="IN_PROGRESS"
    )

    mock_session.exec.return_value.first.return_value = rental

    # Send request to cancel rental
    response = client.put(f"/api/v1/rentals/{rental_uid}/cancel", headers={"X-User-Name": username})

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELED"


def test_finish_rental(client, mock_session):
    """Test the PUT /api/v1/rentals/{rental_uid}/finish endpoint."""
    rental_uid = uuid4()

    # Mock the rental data
    rental = Rental(
        rental_uid=rental_uid,
        username="testuser",
        payment_uid=uuid4(),
        car_uid=uuid4(),
        date_from=datetime(2024, 1, 1),
        date_to=datetime(2024, 1, 10),
        status="IN_PROGRESS"
    )

    mock_session.exec.return_value.first.return_value = rental

    # Send request to finish rental
    response = client.put(f"/api/v1/rentals/{rental_uid}/finish")

    assert response.status_code == 200
    assert response.json()["status"] == "FINISHED"


def test_request_validation_error(client):
    """Test custom request validation exception handler."""
    # Send a request with invalid field (e.g., non-UUID rental_uid)
    response = client.put("/api/v1/rentals/invalid-uuid/cancel", json={})

    assert response.status_code == 400
    assert "what" in response.json()
    assert "errors" in response.json()


