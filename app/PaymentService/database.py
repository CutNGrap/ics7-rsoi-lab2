from sqlmodel import SQLModel, Field, Column, CheckConstraint
import uuid

class Payment(SQLModel, table=True):
    __tablename__ = "payment"
    __table_args__ = (
        CheckConstraint("status IN ('PAID', 'CANCELED')", name="status_check"),  # Создаем ограничение
    )

    id: int = Field(primary_key=True, index=True)
    payment_uid: uuid.UUID = Field(default_factory=uuid.uuid4, nullable=False)
    status: str = Field(nullable=False)
    price: int = Field(nullable=False)

class PaymentDataJson(SQLModel):
    payment_uid: str
    status: str
    price: int

