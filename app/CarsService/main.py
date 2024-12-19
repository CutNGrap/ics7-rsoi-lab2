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


database_url = os.environ["DATABASE_URL"]
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
    return Response(status_code=200)

@app.get("/api/v1/cars", response_model=list[CarDataJson])
def get_all_cars(
    session: Session, 
    page: int = Query(1, alias="page", ge=1), 
    size: int = Query(10, alias="size", ge=1), 
    showAll: bool = Query(False, alias="showAll")
):
    query = select(Car)
    if not showAll:
        query = query.where(Car.availability == True)

    cars = session.exec(query.offset((page - 1) * size).limit(size)).all()
    if not cars:
        raise HTTPException(status_code=404, detail="No cars available")

    return [
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
    ]



@app.put("/api/v1/cars/{car_uid}/reserve", status_code=200, response_model=CarReserveResponse)
def reserve_car(car_uid: uuid.UUID, session: SessionDep):
    """
    Endpoint for reserving a car by setting its availability to False.
    """
    # Fetch the car by UUID
    car = session.exec(select(Car).where(Car.car_uid == car_uid)).first()

    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    if not car.availability:
        raise HTTPException(status_code=400, detail="Car is already reserved")

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
def release_car(car_uid: uuid.UUID, session: SessionDep):
    """
    Endpoint for releasing a car by setting its availability to True.
    """
    car = session.exec(select(Car).where(Car.car_uid == car_uid)).first()

    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    if car.availability:
        raise HTTPException(status_code=400, detail="Car is already available")

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