from sqlmodel import SQLModel, Field, Column, CheckConstraint
import uuid

class Payment(SQLModel, table=True):
    __tablename__ = "payment"

    id: int = Field(primary_key=True, index=True)
    payment_uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False)
    status: str = Field(
        sa_column=Column(
            "status", 
            nullable=False, 
            check=CheckConstraint("status IN ('PAID', 'CANCELED')")
        )
    )
    price: int = Field(nullable=False)

class PaymentDataJson(SQLModel):
    payment_uid: str
    status: str
    price: int

