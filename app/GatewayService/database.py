from sqlmodel import SQLModel, Field, Column, CheckConstraint
import uuid

class CarData(SQLModel):
    car_uid: str
    brand: str
    model: str
    registration_number: str
    power: int
    price: int
    type: str
    availability: bool


class GetCarsResponse(SQLModel):
    page: int
    pageSize: int
    totalElements: int
    items: list[CarData]

class RentalRequest(BaseModel):
    car_id: UUID
    start_date: str
    end_date: str
    payment_method: str