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
from http import HTTPStatus
import requests
from datetime import datetime
import uuid

# carsApi = "localhost:8070/api/v1"
# rentalsApi = "localhost:8060/api/v1"
# paymentsApi = "localhost:8050/api/v1"

carsHost = "cars:8070"


carsApi = "cars:8070/api/v1"
rentalsApi = "rentals:8060/api/v1"
paymentsApi = "payments:8050/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    requests.post(f"http://{carsHost}/manage/init")
    yield  

app = FastAPI(lifespan=lifespan)


@app.get('/manage/health', status_code=200)
def health_check():
    return


# Base URLs for services


@app.get("/api/v1/cars", response_model=PaginationResponse)
def get_cars(
    page: int = Query(1, ge=0),
    size: int = Query(10, ge=1, le=100),
    showAll: bool = Query(False)
) -> PaginationResponse:
    response = requests.get(f"http://{carsApi}/cars", params={"page": page, "size": size})
    print(response.json())
    out: PaginationResponse = PaginationResponse(**response.json())
    if response.status_code == HTTPStatus.OK:
        return out
    else:
        return PaginationResponse(page=page, size=size, totalElements=0, items=[])
    

@app.get("/api/v1/rental", response_model=list[RentalResponse])
def get_user_rentals(
    username: Annotated[str, Header(alias="X-User-Name")]
):
    """
    Gateway метод для получения информации обо всех арендах пользователя.
    """
    try:
        # Отправка запроса к сервису RentalsService
        response = requests.get(f"http://{rentalsApi}/rentals", headers={"X-User-Name": username})
        
        if response.status_code == HTTPStatus.OK:
            ans = []
            rentals = response.json()
            for rental in rentals:

                carUid = rental["carUid"]
                paymentUid = rental["paymentUid"]

                carResponse = requests.get(
                    f"http://{carsApi}/cars/{carUid}?showAll=true"
                )

                if carResponse.status_code != HTTPStatus.OK:
                    raise HTTPException(status_code=404, detail="Couldnt finde car")
                
                payResponse = requests.get(
                    f"http://{paymentsApi}/payment/{paymentUid}"
                )

                if payResponse.status_code != HTTPStatus.OK:
                    raise HTTPException(status_code=404, detail="Couldnt finde payment")


                carData = carResponse.json()
                payData= payResponse.json()

                ans.append(RentalResponse(
                    rentalUid=rental["rentalUid"],
                    status = rental["status"],
                    dateFrom = rental["dateFrom"],
                    dateTo = rental["dateTo"],
                    car = CarData(
                        carUid = carData["carUid"],
                        brand = carData["brand"],
                        model = carData["model"],
                        registrationNumber = carData["registrationNumber"]
                    ),
                    payment=PaymentData(
                        paymentUid = paymentUid,
                        status = payData["status"],
                        price = payData["price"],
                    )
                ))

            return ans
        elif response.status_code == HTTPStatus.NOT_FOUND:
            raise HTTPException(status_code=404, detail="No rentals found for user")
        else:
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with RentalsService: {str(e)}")


@app.get("/api/v1/rental/{rentalUid}", response_model=RentalResponse)
def get_rental_details(
    rentalUid: str,
    username: Annotated[str, Header(alias="X-User-Name")]
):
    """
    Gateway метод для получения информации по конкретной аренде пользователя.
    """
    try:
        # Формирование запроса к RentalsService
        response = requests.get(
            f"http://{rentalsApi}/rentals/{rentalUid}",
            headers={"X-User-Name": username}
        )
        
        if response.status_code == HTTPStatus.OK:
            rental = response.json()
            carUid = rental["carUid"]
            paymentUid = rental["paymentUid"]

            carResponse = requests.get(
                f"http://{carsApi}/cars/{carUid}?showAll=true"
            )

            if carResponse.status_code != HTTPStatus.OK:
                raise HTTPException(status_code=404, detail="Couldnt finde car")
            
            payResponse = requests.get(
                f"http://{paymentsApi}/payment/{paymentUid}"
            )

            if payResponse.status_code != HTTPStatus.OK:
                raise HTTPException(status_code=404, detail="Couldnt finde payment")


            carData = carResponse.json()
            payData= payResponse.json()

            return RentalResponse(
                rentalUid=rental["rentalUid"],
                status = rental["status"],
                dateFrom = rental["dateFrom"],
                dateTo = rental["dateTo"],
                car = CarData(
                    carUid = carData["carUid"],
                    brand = carData["brand"],
                    model = carData["model"],
                    registrationNumber = carData["registrationNumber"]
                ),
                payment=PaymentData(
                    paymentUid = paymentUid,
                    status = payData["status"],
                    price = payData["price"],
                )
            )
        elif response.status_code == HTTPStatus.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Rental not found")
        elif response.status_code == HTTPStatus.FORBIDDEN:
            raise HTTPException(status_code=403, detail="Unauthorized to access this rental")
        else:
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with RentalsService: {str(e)}")
    

@app.post("/api/v1/rental", status_code=200)
def book_car(
    rental_request: CreateRentalRequest, 
    username: Annotated[str, Header(alias="X-User-Name")]
) -> CreateRentalResponse:
    """
    Gateway метод для бронирования автомобиля.
    """
    try:
        # Проверяем, существует ли автомобиль
        carUid = rental_request.carUid
        response = requests.get(f"http://{carsApi}/cars/{carUid}")
        if response.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=404, detail="Car not found")

        car = response.json()
        # if not car["availability"]:
        #     raise HTTPException(status_code=400, detail="Car is already reserved")

        # Резервируем автомобиль
        reserve_response = requests.put(
            f"http://{carsApi}/cars/{carUid}/reserve"
        )
        if reserve_response.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=500, detail="Failed to reserve car")

        # Считаем количество дней аренды
        date_from = datetime.strptime(str(rental_request.dateFrom), "%Y-%m-%d")
        date_to = datetime.strptime(str(rental_request.dateTo), "%Y-%m-%d")
        rental_days = (date_to - date_from).days

        if rental_days <= 0:
            raise HTTPException(status_code=400, detail="Invalid rental period")

        # Рассчитываем стоимость аренды
        total_price = rental_days * car["price"]

        # Создаем запись в Payment Service
        payment_request = {
            "status": "PAID",
            "price": total_price
        }
        payment_response = requests.post(
            f"http://{paymentsApi}/payment", json=payment_request
        )
        
        # if payment_response.status_code != HTTPStatus.CREATED:
        #     raise HTTPException(status_code=500, detail="Failed to create payment")

        payment_data = payment_response.json()


        # Создаем запись в Rental Service
        rental_data = {
            "rentalUid": str(uuid.uuid4()),
            "username": username,
            "paymentUid": str(payment_data["paymentUid"]),
            "carUid": str(carUid),
            "date_from": str(rental_request.dateFrom),
            "date_to": str(rental_request.dateTo),
            "status": "IN_PROGRESS"
        }

        rental_response = requests.post(
            f"http://{rentalsApi}/rentals", json=rental_data
        )

        if rental_response.status_code != HTTPStatus.CREATED:
            raise HTTPException(status_code=500, detail="Failed to create rental record")
        
        rental_response_data =  rental_response.json()
        
        p = PaymentInfo(
                paymentUid=str(payment_data['paymentUid']),
                status=payment_data["status"],
                price=payment_data["price"]
            )
        
        uid = str(rental_response_data["rentalUid"])

        ans = CreateRentalResponse(
            rentalUid=uid,
            status=rental_response_data["status"],
            carUid=str(carUid),
            dateFrom=date_from,
            dateTo=date_to,
            payment=p
        )

        return ans
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with services: {str(e)}")

@app.post("/api/v1/rental/{rentalUid}/finish", status_code=204)
def finish_rental(
    rentalUid: str,
    username: Annotated[str, Header(alias="X-User-Name")]
):
    """
    Завершение аренды автомобиля.
    С автомобиля снимается резерв.
    В Rental Service аренда помечается завершенной (статус FINISHED).
    """
    try:
        # Check if rental exists in Rental Service
        rental_response = requests.get(f"http://{rentalsApi}/rentals/{rentalUid}",
                                       headers={"X-User-Name": username})
        
        if rental_response.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=404, detail="Rental not found")
        
        rental_data = rental_response.json()
        
        # Check if the rental is already finished
        if rental_data['status'] == 'FINISHED':
            raise HTTPException(status_code=400, detail="Rental is already finished")
        
        # Update rental status to 'FINISHED' in Rental Service
        finish_rental_data = {
            "status": "FINISHED"
        }
        finish_response = requests.put(
            f"http://{rentalsApi}/rentals/{rentalUid}/finish", 
            json=finish_rental_data
        )
        if finish_response.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=500, detail="Failed to update rental status")
        
        # Remove reservation on the car in Car Service
        carUid = rental_data["carUid"]
        unreserve_response = requests.put(
            f"http://{carsApi}/cars/{carUid}/release"
        )
        if unreserve_response.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=500, detail="Failed to unreserve car")
        
        return 
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with services: {str(e)}")

from fastapi import HTTPException, Header
from http import HTTPStatus
import requests
from typing import Annotated

@app.delete("/api/v1/rental/{rentalUid}", status_code=204)
def cancel_rental(
    rentalUid: str,
    username: Annotated[str, Header(alias="X-User-Name")]
):
    """
    Отмена аренды автомобиля.
    С автомобиля снимается резерв.
    В Rental Service аренда помечается отмененной (статус CANCELED).
    В Payment Service запись об оплате помечается отмененной (статус CANCELED).
    """
    try:
        # Step 1: Get rental information from Rental Service
        rental_response = requests.get(f"http://{rentalsApi}/rentals/{rentalUid}",
                                       headers={"X-User-Name": username})
        
        if rental_response.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=404, detail="Rental not found")
        
        rental_data = rental_response.json()
        
        # # Check if the rental is already canceled
        # if rental_data['status'] == 'CANCELED':
        #     raise HTTPException(status_code=400, detail="Rental is already canceled")

        # Remove reservation on the car in Car Service

        carUid = rental_data["carUid"]
        print('\n\n',carUid,'\n\n')
        unreserve_response = requests.put(
            f"http://{carsApi}/cars/{carUid}/release"
        )
        if unreserve_response.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=500, detail="Failed to unreserve car")
        
        # Step 3: Cancel the rental in Rental Service by updating status to 'CANCELED'
        cancel_rental_data = {
            "status": "CANCELED"
        }
        rental_finish_response = requests.put(
            f"http://{rentalsApi}/rentals/{rentalUid}/cancel",
            json=cancel_rental_data,
            headers={"X-User-Name": username}  # Include the username header
        )
        
        if rental_finish_response.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=500, detail="Failed to update rental status to CANCELED")
        
        # Step 4: Cancel the payment in Payment Service
        paymentUid = rental_data['paymentUid']  # Assuming we get paymentUid from rental data
        cancel_payment_data = {
            "status": "CANCELED"
        }
        payment_response = requests.put(
            f"http://{paymentsApi}/payments/{paymentUid}/cancel",
            json=cancel_payment_data,
            headers={"X-User-Name": username}  # Include the username header
        )
        
        if payment_response.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=500, detail="Failed to update payment status to CANCELED")
        
        return 
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with services: {str(e)}")

