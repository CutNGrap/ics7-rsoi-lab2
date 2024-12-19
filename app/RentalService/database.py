from sqlmodel import SQLModel, Field, Column, CheckConstraint
import uuid
import datetime as dt

class Rental(SQLModel, table=True):
    __tablename__ = "rental"

    id: int = Field(primary_key=True, index=True)
    rental_uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False, unique=True)
    username: str = Field(nullable=False, max_length=80)
    payment_uid: uuid.UUID = Field(nullable=False)
    car_uid: uuid.UUID = Field(nullable=False)
    date_from: dt.datetime = Field(nullable=False)
    date_to: dt.datetime = Field(nullable=False)
    status: str = Field(
        sa_column=Column(
            "status", 
            nullable=False, 
            check=CheckConstraint("status IN ('IN_PROGRESS', 'FINISHED', 'CANCELED')")
        )
    )


class RentalDataJSON(SQLModel):
    rental_uid: str
    username: str
    payment_uid: str
    car_uid: str
    date_from: datetime.datetime
    date_to: datetime.datetime
    status: str