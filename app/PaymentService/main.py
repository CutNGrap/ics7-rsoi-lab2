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

database_url = database_url = 'postgresql://program:test@localhost:5432/payments'
# database_url = os.environ["DATABASE_URL"]
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

@app.post("/api/v1/payments", status_code=201, response_model=PaymentDataJson)
def create_payment(payment: Payment, session: SessionDep):
    """
    Endpoint for creating a new payment record.
    """
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return PaymentDataJson(
        payment_uid=str(payment.payment_uid),
        status=payment.status,
        price=payment.price
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request : Request, exc):
    return JSONResponse({"message": "what", "errors": exc.errors()[0]}, status_code=400)


