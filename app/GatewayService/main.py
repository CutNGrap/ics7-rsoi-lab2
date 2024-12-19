from fastapi import *
from fastapi.responses import *
from fastapi.exceptions import RequestValidationError
from sqlmodel import *
from database import *
from typing import Annotated
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
import uvicorn
from multiprocessing import Process
import os
import requests
from http import HTTPStatus

carsHost = "cars:8070"
rentalsHost = "rentals:8060"
paymentsHost = "payments:8070"
carsApi = f"{carsHost}/api/v1"
rentalsApi = f"{rentalsHost}/api/v1"
paymentsApi = f"{paymentsHost}/api/v1"

@asynccontextmanager
async def lifespan(app: FastAPI):
    pass

app = FastAPI(lifespan=lifespan)


@app.get('/manage/health', status_code=200)
def health_check():
    return


# Base URLs for services
cars_host = "http://cars:8070/api/v1"
rentals_host = "http://rentals:8060/api/v1"
payments_host = "http://payments:8070/api/v1"


@app.get("/api/v1/cars")
def get_cars(
    page: int = Query(1, ge=0),
    size: int = Query(10, ge=1, le=100),
    showAll: bool = Query(False)
):
    """
    Получить список всех доступных для бронирования автомобилей.
    """
    params = {"page": page, "size": size, "showAll": showAll}
    response = requests.get(f"{cars_host}/cars", params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return response.json()


@app.get("/api/v1/rental")
def get_user_rentals(x_user_name: str = Header(...)):
    """
    Получить информацию о всех арендах пользователя.
    """
    headers = {"X-User-Name": x_user_name}
    response = requests.get(f"{rentals_host}/rentals", headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return response.json()


@app.post("/api/v1/rental")
def create_rental(
    rental_request: RentalRequest,
    x_user_name: str = Header(...)
):
    """
    Забронировать автомобиль.
    """
    headers = {"X-User-Name": x_user_name}
    response = requests.post(f"{rentals_host}/rentals", json=rental_request.dict(), headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return response.json()


@app.get("/api/v1/rental/{rental_uid}")
def get_rental(
    rental_uid: UUID, x_user_name: str = Header(...)
):
    """
    Информация по конкретной аренде пользователя.
    """
    headers = {"X-User-Name": x_user_name}
    response = requests.get(f"{rentals_host}/rentals/{rental_uid}", headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    return response.json()


@app.delete("/api/v1/rental/{rental_uid}", status_code=204)
def cancel_rental(
    rental_uid: UUID, x_user_name: str = Header(...)
):
    """
    Отмена аренды автомобиля.
    """
    headers = {"X-User-Name": x_user_name}
    response = requests.delete(f"{rentals_host}/rentals/{rental_uid}", headers=headers)

    if response.status_code != 204:
        raise HTTPException(status_code=response.status_code, detail=response.json())


@app.post("/api/v1/rental/{rental_uid}/finish", status_code=204)
def finish_rental(
    rental_uid: UUID, x_user_name: str = Header(...)
):
    """
    Завершение аренды автомобиля.
    """
    headers = {"X-User-Name": x_user_name}
    response = requests.post(f"{rentals_host}/rentals/{rental_uid}/finish", headers=headers)

    if response.status_code != 204:
        raise HTTPException(status_code=response.status_code, detail=response.json())
