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
import datetime as dt
import uuid

app = FastAPI()


# database_url = os.environ["DATABASE_URL"]
# database_url = 'postgresql://program:test@localhost/cars'
# database_url = 'postgresql://program:test@localhost/cars'
database_url = 'postgresql://program:test@autorack.proxy.rlwy.net:52848/cars'
print(database_url)
engine = create_engine(database_url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)


@app.get('/manage/health', status_code=200) 
def health():
    return 

@app.post("/api/v1/init", status_code=201)
def init_car(session: Session = Depends(get_session)):
    # Данные машины
    car_data = Car(
        car_uid=uuid.UUID("109b42f3-198d-4c89-9276-a7520a7120ab"),
        brand="Mercedes Benz",
        model="GLA 250",
        registration_number="ЛО777Х799",
        power=249,
        price=3500,
        type="SEDAN",
        availability=True
    )

    # Проверка на уникальность car_uid
    existing_car = session.exec(select(Car).where(Car.car_uid == car_data.car_uid)).first()
    if existing_car:
        raise HTTPException(status_code=400, detail="Car with this car_uid already exists.")

    # Добавляем машину в базу данных
    session.add(car_data)
    session.commit()
    session.refresh(car_data)

    return {
        "message": "Car added successfully",
        "car": {
            "car_uid": str(car_data.car_uid),
            "brand": car_data.brand,
            "model": car_data.model,
            "registration_number": car_data.registration_number,
            "power": car_data.power,
            "price": car_data.price,
            "type": car_data.type,
            "availability": car_data.availability
        }
    }

@app.get("/api/v1/cars", response_model=CarsResponse)
def get_all_cars(
    session: SessionDep, 
    page: int = Query(1, alias="page", ge=1), 
    size: int = Query(10, alias="size", ge=1), 
    showAll: bool = Query(False, alias="showAll")
) -> CarsResponse:
    query = select(Car)
    if not showAll:
        query = query.where(Car.availability == True)

    cars = session.exec(query.offset((page - 1) * size).limit(size)).all()
    if not cars:
        raise HTTPException(status_code=404, detail="No cars available")

    response_data = CarsResponse(
        items=[
            CarDataJson(
                car_uid=str(car.car_uid),
                brand=car.brand,
                model=car.model,
                registration_number=car.registration_number,
                power=car.power,
                price=car.price,
                type=car.type,
                availability=car.availability
            ) for car in cars
        ],
        totalElements=len(cars)  # Optionally include the total count of cars
    )

    return response_data

@app.get("/api/v1/cars/{car_uid}", response_model=CarDataJson)
def get_car(session: SessionDep, car_uid: str):
    """
    Возвращает информацию об автомобиле по его car_uid.
    """
    query = select(Car).where(Car.car_uid==car_uid)
    car = session.exec(query).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return CarDataJson(
                car_uid=str(car.car_uid),
                brand=car.brand,
                model=car.model,
                registration_number=car.registration_number,
                power=car.power,
                price=car.price,
                type=car.type,
                availability=car.availability
            )


@app.put("/api/v1/cars/{car_uid}/reserve", status_code=200, response_model=CarReserveResponse)
def reserve_car(car_uid: uuid.UUID, session: SessionDep) -> CarReserveResponse:
    """
    Endpoint for reserving a car by setting its availability to False.
    """
    # Fetch the car by UUID
    car = session.exec(select(Car).where(Car.car_uid == car_uid)).first()

    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    # if not car.availability:
    #     raise HTTPException(status_code=400, detail="Car is already reserved")

    # Update the availability
    car.availability = False
    session.add(car)
    session.commit()
    session.refresh(car)

    return CarReserveResponse(
        message="Car reserved successfully",
        car_uid=str(car.car_uid),
        availability=car.availability
    )


@app.put("/api/v1/cars/{car_uid}/release", status_code=200, response_model=CarReserveResponse)
def release_car(car_uid: uuid.UUID, session: SessionDep) -> CarReserveResponse:
    """
    Endpoint for releasing a car by setting its availability to True.
    """
    car = session.exec(select(Car).where(Car.car_uid == car_uid)).first()

    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    # if car.availability:
    #     raise HTTPException(status_code=400, detail="Car is already available")

    car.availability = True
    session.add(car)
    session.commit()
    session.refresh(car)

    return CarReserveResponse(
        message="Car released successfully",
        car_uid=str(car.car_uid),
        availability=car.availability
    )




@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request : Request, exc):
    return JSONResponse({"message": "what", "errors": exc.errors()[0]}, status_code=400)