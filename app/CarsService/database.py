from sqlmodel import SQLModel, Field, Column, CheckConstraint
import uuid

class Car(SQLModel, table=True):
    __tablename__ = "cars"

    id: int = Field(primary_key=True, index=True)
    car_uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, unique=True)
    brand: str = Field(nullable=False, max_length=80)
    model: str = Field(nullable=False, max_length=80)
    registration_number: str = Field(nullable=False, max_length=20)
    power: int = Field(default=None)
    price: int = Field(nullable=False)
    type: str = Field(
        sa_column=Column(
            "type", 
            nullable=True, 
            check=CheckConstraint("type IN ('SEDAN', 'SUV', 'MINIVAN', 'ROADSTER')")
        )
    )
    availability: bool = Field(nullable=False)

class CarDataJSON(SQLModel):
    car_uid: str
    brand: str
    model: str
    registration_number: str
    power: int
    price: int
    type: str
    availability: bool
